"""Retrieval pipeline job — runs entirely inside an ARQ worker.

Loads investigation and execution state from the database, executes
the pipeline stages, and persists results.  Never exposed to HTTP;
all inputs come from the job payload and the database.
"""

import os
import socket
import uuid
from datetime import UTC, datetime

from arq.connections import JobResult
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import SessionLocal
from app.modules.analysis.service.service import AnalysisService
from app.modules.artifact.service.service import ArtifactService
from app.modules.execution.domain.models import ExecutionStatus
from app.modules.execution.schemas.request import UpdateExecutionRequest
from app.modules.execution.service.service import (
    ExecutionService,
    ExecutionStageService,
)
from app.modules.extraction.llm import ProviderFactory
from app.modules.extraction.service.service import ExtractionService
from app.modules.gap_detection.service.service import GapDetectionService
from app.modules.investigation.timeline.models import TimelineStage, TimelineStatus
from app.modules.investigation.timeline.service import TimelineService
from app.modules.paper.service.service import PaperService
from app.modules.retrieval.service.service import RetrievalService
from app.modules.validation.service.service import ValidationService
from app.observability.logger import get_logger
from app.pipeline import PipelineContext
from app.plugins import registry

logger = get_logger(__name__)

MAX_RETRIES = 4  # Original attempt + 3 retries


def _mark_terminal(
    execution_id: uuid.UUID,
    status: ExecutionStatus,
) -> None:
    """Mark an execution as terminal in a fresh session."""
    with SessionLocal() as session:
        try:
            ExecutionService(session).update_execution(
                execution_id,
                UpdateExecutionRequest(status=status),
            )
            session.commit()
        except Exception:
            logger.exception("failed_to_mark_execution", execution_id=str(execution_id))


async def retrieval_job(
    ctx: dict,
    execution_id: uuid.UUID,
    investigation_id: uuid.UUID,
    query: str,
    paper_limit: int = 10,
) -> JobResult:
    """Execute the retrieval pipeline inside an ARQ worker.

    Parameters are loaded from the database — never trust a frontend
    payload to contain authoritative data beyond the initial query.

    Retry policy (exponential backoff, max 3 retries)::

        attempt 1 →  5s delay
        attempt 2 → 10s delay
        attempt 3 → 20s delay
        attempt 4 → permanent FAILED
    """
    attempt = ctx.get("job_try", 1)
    exec_id = str(execution_id)
    inv_id = str(investigation_id)

    logger.info(
        "retrieval_job_started",
        execution_id=exec_id,
        investigation_id=inv_id,
        attempt=attempt,
        query=query,
    )

    session: Session = SessionLocal()
    try:
        # ── Init services ────────────────────────────────────────
        execution_service = ExecutionService(session)
        stage_service = ExecutionStageService(session)
        timeline_service = TimelineService(session)
        artifact_service = ArtifactService(session)
        paper_service = PaperService(session)
        retrieval_service = RetrievalService()
        validation_service = ValidationService()
        llm_provider = ProviderFactory.create(get_settings().LLM_PROVIDER)
        extraction_service = ExtractionService(
            session=session,
            llm_provider=llm_provider,
        )
        analysis_service = AnalysisService(session=session)
        gap_detection_service = GapDetectionService(session=session)

        # ── Load state ───────────────────────────────────────────
        execution = execution_service.get_execution(execution_id)
        if execution is None:
            logger.error("execution_not_found", execution_id=exec_id)
            return JobResult()

        if execution.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ):
            logger.info(
                "execution_already_terminal",
                execution_id=exec_id,
                status=execution.status.value,
            )
            return JobResult()

        # ── Mark RUNNING (first attempt only) ────────────────────
        if attempt == 1:
            execution_service.update_execution(
                execution_id,
                UpdateExecutionRequest(status=ExecutionStatus.RUNNING),
            )
            timeline_service.record_event(
                investigation_id=investigation_id,
                execution_id=execution_id,
                stage=TimelineStage.RETRIEVING,
                status=TimelineStatus.RUNNING,
                message="Paper retrieval started",
            )
            timeline_service.record_event(
                investigation_id=investigation_id,
                execution_id=execution_id,
                stage=TimelineStage.VALIDATING,
                status=TimelineStatus.RUNNING,
                message="Validation started",
            )
            timeline_service.record_event(
                investigation_id=investigation_id,
                execution_id=execution_id,
                stage=TimelineStage.EXTRACTING,
                status=TimelineStatus.RUNNING,
                message="Knowledge extraction started",
            )
            timeline_service.record_event(
                investigation_id=investigation_id,
                execution_id=execution_id,
                stage=TimelineStage.ANALYZING,
                status=TimelineStatus.RUNNING,
                message="Cross-paper analysis started",
            )
            session.commit()

            # ── Write worker metadata ────────────────────────────
            job_id = ctx.get("job_id", "")
            queue_name = ctx.get("redis", {}).get("queue_name", "arq:default")
            execution_service.update_metadata(
                execution_id,
                {
                    "worker_hostname": socket.gethostname(),
                    "worker_pid": os.getpid(),
                    "job_id": job_id,
                    "queue_name": queue_name,
                },
            )

        # ── Build pipeline ───────────────────────────────────────
        context = PipelineContext(
            investigation_id=investigation_id,
            execution_id=execution_id,
        )
        context.set_metadata("query", query)
        context.set_metadata("paper_limit", paper_limit)
        context.set_metadata("timeline_stage", "retrieving")

        definition = registry.get_pipeline(
            "retrieval",
            stage_recorder=stage_service,
            retrieval_service=retrieval_service,
            validation_service=validation_service,
            paper_service=paper_service,
            artifact_service=artifact_service,
            extraction_service=extraction_service,
            analysis_service=analysis_service,
            gap_detection_service=gap_detection_service,
            timeline_service=timeline_service,
        )

        # ── Execute ──────────────────────────────────────────────
        start = datetime.now(UTC)
        final_context = await definition.run(context)
        elapsed = (datetime.now(UTC) - start).total_seconds()

        # ── Handle result ────────────────────────────────────────
        if final_context.execution_state.get("failed_at"):
            _mark_terminal(execution_id, ExecutionStatus.FAILED)
            timeline_service.record_event(
                investigation_id=investigation_id,
                execution_id=execution_id,
                stage=TimelineStage.RETRIEVING,
                status=TimelineStatus.FAILURE,
                message="Retrieval failed",
            )
            session.commit()
            logger.error(
                "retrieval_pipeline_failed",
                execution_id=exec_id,
                duration_seconds=round(elapsed, 2),
                errors=final_context.errors,
            )
            return JobResult()

        # ── Persist retrieval metrics to execution metadata ───────
        retrieval_metrics = final_context.metrics.get("retrieval")
        if retrieval_metrics:
            execution_service.update_metadata(
                execution_id,
                {"retrieval_metrics": retrieval_metrics},
            )

        # ── Success ──────────────────────────────────────────────
        execution_service.update_execution(
            execution_id,
            UpdateExecutionRequest(status=ExecutionStatus.COMPLETED),
        )
        session.commit()

        paper_count = final_context.metrics.get("paper_count", 0)
        logger.info(
            "retrieval_pipeline_completed",
            execution_id=exec_id,
            duration_seconds=round(elapsed, 2),
            paper_count=paper_count,
        )
        return JobResult()

    except Exception as exc:
        session.rollback()
        logger.exception(
            "retrieval_job_exception",
            execution_id=exec_id,
            attempt=attempt,
            max_retries=MAX_RETRIES,
            error=str(exc),
        )

        if attempt >= MAX_RETRIES:
            _mark_terminal(execution_id, ExecutionStatus.FAILED)
            logger.error(
                "retrieval_job_failed_permanent",
                execution_id=exec_id,
                attempt=attempt,
            )
            return JobResult()

        delay = 2 ** (attempt - 1) * 5
        logger.warning(
            "retrieval_job_scheduling_retry",
            execution_id=exec_id,
            attempt=attempt,
            delay_seconds=delay,
        )
        return JobResult(retry_delay=delay)

    finally:
        session.close()
