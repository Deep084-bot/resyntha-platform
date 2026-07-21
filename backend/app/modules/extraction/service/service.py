"""Orchestrates LLM-based knowledge extraction for a set of papers.

``ExtractionService`` is instantiated *per run* (stateless) and
handles: fetching papers from the repository → calling the LLM
provider → parsing → persisting → creating a ``KNOWLEDGE_PACKAGE``
artifact.
"""

import asyncio
import json
import uuid
from collections import Counter

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.llm import (
    BaseLLMProvider,
    LLMAPIError,
    LLMParsingError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.modules.extraction.domain.knowledge import ExtractionOutput
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.extraction.domain.results import (
    ExtractionBatchResult,
    ExtractionFailure,
    ExtractionStats,
    FailureReason,
)
from app.modules.extraction.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
)
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.extraction.service.artifact import ExtractionArtifactBuilder
from app.modules.extraction.utils.normalization import ExtractionNormalizer
from app.modules.extraction.utils.validation import ExtractionValidator
from app.modules.paper.domain.models import Paper
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

        semaphore = asyncio.Semaphore(5)

        async def extract_one(paper):
            async with semaphore:
                try:
                    result = await self._extract_single(
                        paper,
                        investigation_id,
                        execution_id,
                    )
                    return result
                except Exception as exc:
                    logger.exception(
                        "extraction_failed",
                        paper_id=str(paper.id),
                        title=paper.title[:100],
                    )
                    return ExtractionFailure(
                        paper_id=paper.id,
                        title=getattr(paper, "title", "Untitled"),
                        reason=FailureReason.UNKNOWN,
                        detail=str(exc)[:500],
                    )

        results = await asyncio.gather(
            *(extract_one(paper) for paper in papers),
        )

        for result in results:
            if isinstance(result, ExtractionFailure):
                failures.append(result)
            else:
                knowledge.append(result)

        reason_counts = Counter(f.reason.value for f in failures)
        stats = ExtractionStats(
            total=len(papers),
            successful=len(knowledge),
            failed=len(failures),
            provider=self._llm.provider_name,
            failure_reasons=dict(reason_counts),
        )

        self._create_knowledge_package_artifact(
            investigation_id,
            knowledge,
            execution_id,
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
        paper: Paper,
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
            output: ExtractionOutput  # type: ignore[assignment]
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
        except LLMRateLimitError as exc:
            logger.error(
                "extraction_rate_limited",
                paper_id=str(paper.id),
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.RATE_LIMIT,
                detail=str(exc)[:500],
            )
        except LLMTimeoutError as exc:
            logger.error(
                "extraction_timed_out",
                paper_id=str(paper.id),
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.TIMEOUT,
                detail=str(exc)[:500],
            )
        except LLMAPIError as exc:
            logger.error(
                "extraction_api_error",
                paper_id=str(paper.id),
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.API_ERROR,
                detail=str(exc)[:500],
            )

        if self._is_low_quality(output):
            logger.warning(
                "extraction_low_quality",
                paper_id=str(paper.id),
                title=title[:100],
                summary_length=len(output.summary),
            )
            return ExtractionFailure(
                paper_id=paper.id,
                title=title,
                reason=FailureReason.LOW_QUALITY_CONTENT,
                detail="LLM returned empty or near-empty content",
            )

        authors_dicts = self._normalize_author_list(output.authors)
        institutions_dicts = self._normalize_institution_list(output.institutions)
        datasets_dicts = self._normalize_dataset_list(output.datasets_used)
        technologies_dicts = self._normalize_technology_list(output.technologies)
        metrics_dicts = self._normalize_metric_list(output.evaluation_metrics)

        valid_authors = ExtractionValidator.filter_valid_entities(
            authors_dicts,
            "author",
            min_confidence=0.3,
        )
        valid_institutions = ExtractionValidator.filter_valid_entities(
            institutions_dicts,
            "institution",
            min_confidence=0.3,
        )
        valid_datasets = ExtractionValidator.filter_valid_entities(
            datasets_dicts,
            "dataset",
            min_confidence=0.3,
        )
        valid_technologies = ExtractionValidator.filter_valid_entities(
            technologies_dicts,
            "technology",
            min_confidence=0.3,
        )
        valid_metrics = ExtractionValidator.filter_valid_entities(
            metrics_dicts,
            "metric",
            min_confidence=0.3,
        )

        author_names = [a["name"] for a in valid_authors if "name" in a]
        if author_names and not getattr(paper, "authors", None):
            paper.authors = author_names
            logger.info(
                "paper_authors_backfilled",
                paper_id=str(paper.id),
                author_count=len(author_names),
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
            authors=valid_authors,
            institutions=valid_institutions,
            datasets_used=valid_datasets,
            technologies=valid_technologies,
            evaluation_metrics=valid_metrics,
            research_domains=output.research_domains,
            keywords=output.keywords,
            paper_type=output.paper_type,
            funding=output.funding,
            model_used=self._model or usage.model,
            tokens_used=usage.total_tokens,
        )

        return self._repository.create(knowledge)

    @staticmethod
    def _is_low_quality(output: ExtractionOutput) -> bool:
        if not output.summary or len(output.summary.strip()) < 20:
            return True
        if (
            not output.research_questions
            and not output.key_findings
            and not output.methodology
        ):
            return True
        return False

    # ── Normalization helpers ─────────────────────────────────────

    @staticmethod
    def _normalize_author_list(authors: list) -> list[dict]:
        """Convert Author Pydantic models to dicts with normalised names."""
        result: list[dict] = []
        for i, author in enumerate(authors):
            name = ""
            if isinstance(author, dict):
                name = author.get("name", "")
            else:
                name = getattr(author, "name", "")
            if not name:
                continue
            normalised = ExtractionNormalizer.normalize_author(name)
            if not normalised:
                continue
            entry: dict = {"name": normalised, "order": i + 1}
            if isinstance(author, dict):
                entry["is_corresponding"] = author.get("is_corresponding")
            else:
                entry["is_corresponding"] = getattr(author, "is_corresponding", None)
            result.append(entry)
        return result

    @staticmethod
    def _normalize_institution_list(institutions: list) -> list[dict]:
        """Convert Institution models to dicts with normalised names."""
        result: list[dict] = []
        for inst in institutions:
            name = ""
            department = None
            country = None
            if isinstance(inst, dict):
                name = inst.get("name", "")
                department = inst.get("department")
                country = inst.get("country")
            else:
                name = getattr(inst, "name", "")
                department = getattr(inst, "department", None)
                country = getattr(inst, "country", None)
            if not name:
                continue
            normalised = ExtractionNormalizer.normalize_institution(name)
            if not normalised:
                continue
            entry: dict = {"name": normalised}
            if department:
                entry["department"] = department
            if country:
                entry["country"] = country
            result.append(entry)
        return result

    @staticmethod
    def _normalize_dataset_list(datasets: list) -> list[dict]:
        """Convert Dataset models to dicts with normalised names."""
        result: list[dict] = []
        for ds in datasets:
            name = ""
            is_public = None
            is_benchmark = None
            if isinstance(ds, dict):
                name = ds.get("name", "")
                is_public = ds.get("is_public")
                is_benchmark = ds.get("is_benchmark")
            else:
                name = getattr(ds, "name", "")
                is_public = getattr(ds, "is_public", None)
                is_benchmark = getattr(ds, "is_benchmark", None)
            if not name:
                continue
            normalised = ExtractionNormalizer.normalize_dataset(name)
            if not normalised:
                continue
            entry: dict = {"name": normalised}
            if is_public is not None:
                entry["is_public"] = is_public
            if is_benchmark is not None:
                entry["is_benchmark"] = is_benchmark
            result.append(entry)
        return result

    @staticmethod
    def _normalize_technology_list(technologies: list) -> list[dict]:
        """Convert Technology models to dicts with normalised names."""
        result: list[dict] = []
        for tech in technologies:
            name = ""
            tech_type = None
            if isinstance(tech, dict):
                name = tech.get("name", "")
                tech_type = tech.get("type")
            else:
                name = getattr(tech, "name", "")
                tech_type = getattr(tech, "type", None)
            if not name:
                continue
            normalised = ExtractionNormalizer.normalize_technology(name)
            if not normalised:
                continue
            entry: dict = {"name": normalised}
            if tech_type:
                entry["type"] = tech_type
            result.append(entry)
        return result

    @staticmethod
    def _normalize_metric_list(metrics: list) -> list[dict]:
        """Convert Metric models to dicts."""
        result: list[dict] = []
        for metric in metrics:
            name = ""
            value = None
            dataset = None
            if isinstance(metric, dict):
                name = metric.get("name", "")
                value = metric.get("value")
                dataset = metric.get("dataset")
            else:
                name = getattr(metric, "name", "")
                value = getattr(metric, "value", None)
                dataset = getattr(metric, "dataset", None)
            if not name:
                continue
            if not ExtractionValidator.is_valid_entity_name(name):
                continue
            entry: dict = {"name": name}
            if value:
                entry["value"] = value
            if dataset:
                entry["dataset"] = dataset
            result.append(entry)
        return result

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
