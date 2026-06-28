"""Validate stage — runs deterministic validation on retrieved papers.

Consumes ``context.artifacts["papers"]`` (list of ``Paper`` DTOs).
Produces ``context.artifacts["validated_papers"]`` (list of
``ValidatedPaper`` dicts).  Validation errors are recorded as
context errors but do NOT fail the pipeline — invalid papers are
still passed downstream with their validation metadata.
"""

from app.modules.validation.service.service import ValidationService
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage


class ValidateStage(PipelineStage):
    """Run all validation rules against retrieved papers."""

    consumes: list[str] = ["papers"]
    produces: list[str] = ["validated_papers"]
    metadata: dict = {
        "description": "Run deterministic validation on retrieved papers",
    }

    def __init__(self, validation_service: ValidationService) -> None:
        self._validation_service = validation_service

    def name(self) -> str:
        return "validate"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        from app.modules.retrieval.domain.paper import Paper

        papers: list[Paper] | None = context.get_artifact("papers")
        if not papers:
            context.add_error("validate", "No papers found in context")
            return PipelineResult.FAILED

        result = self._validation_service.validate_papers(papers)

        context.add_artifact("validated_papers", result.validated_papers)
        context.record_metric("validation_total", result.summary.total_papers)
        context.record_metric("validation_valid", result.summary.valid)
        context.record_metric("validation_warning", result.summary.warning)
        context.record_metric("validation_invalid", result.summary.invalid)
        context.record_metric("validation_duplicates", result.summary.duplicates)
        context.record_metric("validation_avg_score", result.summary.average_score)

        if result.summary.invalid > 0:
            context.add_error(
                "validate",
                f"{result.summary.invalid} paper(s) marked INVALID",
            )

        if result.summary.warning > 0:
            context.add_error(
                "validate",
                f"{result.summary.warning} paper(s) marked WARNING",
            )

        return PipelineResult.SUCCESS
