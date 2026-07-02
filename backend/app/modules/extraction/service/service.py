"""Orchestrates LLM-based knowledge extraction for a set of papers.

``ExtractionService`` is instantiated *per run* (stateless) and
handles: fetching papers from the repository → calling the LLM
provider → parsing → persisting → creating a ``KNOWLEDGE_PACKAGE``
artifact.
"""

import json
import uuid
from collections import Counter

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.modules.extraction.domain.knowledge import ExtractionOutput
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.extraction.domain.results import (
    ExtractionBatchResult,
    ExtractionFailure,
    ExtractionStats,
    FailureReason,
)
from app.modules.extraction.llm.base import BaseLLMProvider
from app.modules.extraction.llm.exceptions import LLMParsingError
from app.modules.extraction.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
)
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.extraction.service.artifact import ExtractionArtifactBuilder
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)


class ExtractionService:
    """Orchestrate extraction for an investigation's papers.

    Parameters
    ----------
    session:
        Async SQLAlchemy session.
    llm_provider:
        The LLM provider to use for generation.
    model:
        Model name override (defaults to provider's configured model).
    """

    def __init__(
        self,
        session: Session,
        llm_provider: BaseLLMProvider,
        model: str | None = None,
    ) -> None:
        self._session = session
        self._llm = llm_provider
        self._model = model or ""
        self._repository = ExtractionRepository(session)
        self._paper_repository = PaperRepository(session)
        self._artifact_builder = ExtractionArtifactBuilder(session)

    async def extract_for_investigation(
        self,
        investigation_id: uuid.UUID,
        execution_id: uuid.UUID | None = None,
    ) -> ExtractionBatchResult:
        """Run extraction on all papers in an investigation.

        Returns an ``ExtractionBatchResult`` with successes, failures,
        and aggregate statistics.  Creates a ``KNOWLEDGE_PACKAGE``
        artifact from successful extractions only.
        """
        papers = self._paper_repository.list_by_investigation(
            investigation_id,
        )
        if not papers:
            logger.info(
                "no_papers_for_extraction",
                investigation_id=str(investigation_id),
            )
            return ExtractionBatchResult(
                knowledge=[],
                failures=[],
                stats=ExtractionStats(
                    total=0,
                    successful=0,
                    failed=0,
                    provider=self._llm.provider_name,
                ),
            )

        knowledge: list[ExtractedKnowledge] = []
        failures: list[ExtractionFailure] = []

        for paper in papers:
            try:
                result = await self._extract_single(
                    paper, investigation_id, execution_id,
                )
                if isinstance(result, ExtractionFailure):
                    failures.append(result)
                else:
                    knowledge.append(result)
            except Exception as exc:
                logger.exception(
                    "extraction_failed",
                    paper_id=str(paper.id),
                    title=paper.title[:100],
                )
                failures.append(
                    ExtractionFailure(
                        paper_id=paper.id,
                        title=getattr(paper, "title", "Untitled"),
                        reason=FailureReason.UNKNOWN,
                        detail=str(exc)[:500],
                    ),
                )

        reason_counts = Counter(f.reason.value for f in failures)
        stats = ExtractionStats(
            total=len(papers),
            successful=len(knowledge),
            failed=len(failures),
            provider=self._llm.provider_name,
            failure_reasons=dict(reason_counts),
        )

        self._create_knowledge_package_artifact(
            investigation_id, knowledge, execution_id,
        )

        self._session.commit()
        logger.info(
            "extraction_complete",
            investigation_id=str(investigation_id),
            count=len(knowledge),
        )
        return ExtractionBatchResult(
            knowledge=knowledge,
            failures=failures,
            stats=stats,
        )

    async def _extract_single(
        self,
        paper: BaseModel,
        investigation_id: uuid.UUID,
        execution_id: uuid.UUID | None,
    ) -> ExtractedKnowledge | ExtractionFailure:
        """Extract knowledge from one paper.

        Returns ``ExtractedKnowledge`` on success or ``ExtractionFailure``
        with a classified reason on any error.  Never returns ``None``.
        """
        title = getattr(paper, "title", "Untitled")
        abstract = getattr(paper, "abstract", "") or ""
        authors = getattr(paper, "authors", "") or ""
        venue = getattr(paper, "venue", "") or ""
        year = getattr(paper, "year", "") or ""
        doi = getattr(paper, "doi", "") or ""

        user_prompt = build_extraction_user_prompt(
            title=title,
            abstract=abstract,
            authors=authors,
            venue=venue,
            year=str(year),
            doi=doi,
        )

        try:
            output, usage = await self._llm.generate_structured(
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=ExtractionOutput,
                max_retries=3,
            )
        except ValidationError as exc:
            logger.error(
                "extraction_llm_error",
                paper_id=str(paper.id),
                error=str(exc)[:300],
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.VALIDATION_ERROR,
                detail=str(exc)[:500],
            )
        except (json.JSONDecodeError, LLMParsingError) as exc:
            logger.error(
                "extraction_llm_error",
                paper_id=str(paper.id),
                error=str(exc)[:300],
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.MALFORMED_JSON,
                detail=str(exc)[:500],
            )
        except RuntimeError as exc:
            reason, detail = self._classify_llm_error(exc)
            logger.error(
                "extraction_llm_error",
                paper_id=str(paper.id),
                error=detail[:300],
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=reason,
                detail=detail,
            )

        knowledge = ExtractedKnowledge(
            investigation_id=investigation_id,
            paper_id=paper.id,
            execution_id=execution_id,
            paper_title=title,
            research_questions=output.research_questions,
            key_findings=output.key_findings,
            methodology=output.methodology,
            limitations=output.limitations,
            key_contributions=output.key_contributions,
            relevant_techniques=output.relevant_techniques,
            cited_works=output.cited_works,
            future_work=output.future_work,
            summary=output.summary,
            model_used=self._model or usage.model,
            tokens_used=usage.total_tokens,
        )

        return self._repository.create(knowledge)

    def _classify_llm_error(
        self,
        exc: RuntimeError,
    ) -> tuple[FailureReason, str]:
        """Classify a ``RuntimeError`` from the LLM provider by inspecting
        ``__cause__``.
        """
        cause = exc.__cause__
        if cause is None:
            return FailureReason.UNKNOWN, str(exc)[:500]

        from groq import APIError, APITimeoutError, RateLimitError

        if isinstance(cause, RateLimitError):
            return FailureReason.RATE_LIMIT, str(cause)[:500]
        if isinstance(cause, APITimeoutError):
            return FailureReason.TIMEOUT, str(cause)[:500]
        if isinstance(cause, APIError):
            return FailureReason.API_ERROR, str(cause)[:500]
        if isinstance(cause, LLMParsingError):
            return FailureReason.MALFORMED_JSON, str(cause)[:500]
        if isinstance(cause, json.JSONDecodeError):
            return FailureReason.MALFORMED_JSON, str(cause)[:500]
        if isinstance(cause, ValidationError):
            return FailureReason.VALIDATION_ERROR, str(cause)[:500]

        return FailureReason.UNKNOWN, str(cause)[:500]

    def _create_knowledge_package_artifact(
        self,
        investigation_id: uuid.UUID,
        results: list[ExtractedKnowledge],
        execution_id: uuid.UUID | None,
    ) -> None:
        """Create a ``KNOWLEDGE_PACKAGE`` artifact summarising results."""
        if not results:
            return
        self._artifact_builder.create_package(
            investigation_id=investigation_id,
            knowledge_records=results,
            execution_id=execution_id,
        )
