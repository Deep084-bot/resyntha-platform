"""Orchestrates LLM-based knowledge extraction for a set of papers.

``ExtractionService`` is instantiated *per run* (stateless) and
handles: fetching papers from the repository → calling the LLM
provider → parsing → persisting → creating a ``KNOWLEDGE_PACKAGE``
artifact.
"""

import uuid

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.modules.extraction.domain.knowledge import ExtractionOutput
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.extraction.llm.base import BaseLLMProvider
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
    ) -> list[ExtractedKnowledge]:
        """Run extraction on all papers in an investigation.

        Returns the list of created ``ExtractedKnowledge`` records
        and creates a ``KNOWLEDGE_PACKAGE`` artifact.
        """
        papers = self._paper_repository.list_by_investigation(
            investigation_id,
        )
        if not papers:
            logger.info(
                "no_papers_for_extraction",
                investigation_id=str(investigation_id),
            )
            return []

        results: list[ExtractedKnowledge] = []
        for paper in papers:
            try:
                knowledge = await self._extract_single(paper, investigation_id, execution_id)
                if knowledge is not None:
                    results.append(knowledge)
            except Exception:
                logger.exception(
                    "extraction_failed",
                    paper_id=str(paper.id),
                    title=paper.title[:100],
                )

        self._create_knowledge_package_artifact(
            investigation_id, results, execution_id,
        )

        self._session.commit()
        logger.info(
            "extraction_complete",
            investigation_id=str(investigation_id),
            count=len(results),
        )
        return results

    async def _extract_single(
        self,
        paper: BaseModel,
        investigation_id: uuid.UUID,
        execution_id: uuid.UUID | None,
    ) -> ExtractedKnowledge | None:
        """Extract knowledge from one paper."""
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
        except (ValidationError, RuntimeError) as exc:
            logger.error(
                "extraction_llm_error",
                paper_id=str(paper.id),
                error=str(exc)[:300],
            )
            return None

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
