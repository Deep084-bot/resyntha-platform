"""Pipeline runner — executes stages sequentially, handles retries,
and returns the final context.

The runner is the heart of the execution engine.  It knows nothing
about retrieval, extraction, or any specific stage — it only knows
how to call ``stage.execute()`` and interpret ``PipelineResult``.
All domain logic lives in the stages themselves.
"""

import asyncio
from collections.abc import Sequence
from datetime import datetime

from app.pipeline.context import PipelineContext
from app.pipeline.exceptions import PipelineException
from app.pipeline.result import PipelineResult
from app.pipeline.retry import RetryPolicy
from app.pipeline.stage import PipelineStage


class PipelineRunner:
    """Orchestrate a sequence of stages, returning the final context.

    Usage::

        runner = PipelineRunner(stages=[RetrieveStage(), ExtractStage()])
        context = PipelineContext(investigation_id=...)
        final = await runner.run(context)
    """

    def __init__(
        self,
        stages: Sequence[PipelineStage],
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._stages = list(stages)
        self._retry_policy = retry_policy or RetryPolicy()

    async def run(self, context: PipelineContext) -> PipelineContext:
        """Execute every stage in order and return the updated context.

        The pipeline stops when a stage returns ``FAILED`` or when all
        retries for a stage are exhausted.  The returned context contains
        any errors and metrics accumulated during execution.
        """
        context.set_state("started_at", datetime.utcnow().isoformat())
        context.set_state("stage_count", len(self._stages))

        for stage in self._stages:
            context.current_stage = stage.name()
            context.set_state("current_stage", stage.name())

            result = await self._execute_stage(stage, context)

            if result == PipelineResult.FAILED:
                context.set_state("failed_at", stage.name())
                break

            context.set_state("last_completed", stage.name())

        context.set_state("finished_at", datetime.utcnow().isoformat())
        context.set_state("error_count", len(context.errors))
        return context

    async def _execute_stage(
        self,
        stage: PipelineStage,
        context: PipelineContext,
    ) -> PipelineResult:
        """Attempt a stage with retries, returning the final result.

        Catches all exceptions from the stage, records them in the
        context, and retries according to the configured policy.
        Returns ``FAILED`` when retries are exhausted.
        """
        last_exception: Exception | None = None
        start = datetime.utcnow()

        for attempt in range(self._retry_policy.max_retries + 1):
            if attempt > 0:
                await self._backoff(attempt)
                context.add_error(
                    stage.name(),
                    f"Retry attempt {attempt}/{self._retry_policy.max_retries}",
                )

            try:
                result = await stage.execute(context)
            except PipelineException:
                raise
            except Exception as exc:
                last_exception = exc
                context.add_error(stage.name(), str(exc), exc)
                continue

            if result == PipelineResult.RETRY and attempt < self._retry_policy.max_retries:
                continue

            duration = (datetime.utcnow() - start).total_seconds()
            context.record_metric(f"{stage.name()}.duration_seconds", duration)
            context.record_metric(f"{stage.name()}.attempts", attempt + 1)

            if result == PipelineResult.RETRY:
                context.add_error(
                    stage.name(),
                    f"Stage returned RETRY {self._retry_policy.max_retries + 1} times",
                )
                return PipelineResult.FAILED

            return result

        duration = (datetime.utcnow() - start).total_seconds()
        context.record_metric(f"{stage.name()}.duration_seconds", duration)
        context.record_metric(f"{stage.name()}.attempts", self._retry_policy.max_retries + 1)
        return PipelineResult.FAILED

    async def _backoff(self, attempt: int) -> None:
        """Sleep for the configured back-off duration."""
        wait = self._retry_policy.backoff_seconds
        if self._retry_policy.exponential_backoff:
            wait *= 2 ** (attempt - 1)
        await asyncio.sleep(wait)
