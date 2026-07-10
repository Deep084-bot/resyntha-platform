"""ARQ worker configuration.

Run with::

    arq app.workers.worker.WorkerSettings
"""

from arq import create_pool
from arq.connections import RedisSettings

from app.config import get_settings
from app.observability.logger import get_logger
from app.workers.retrieval_job import retrieval_job

logger = get_logger(__name__)

settings = get_settings()


def _redis_settings() -> RedisSettings | None:
    """Create RedisSettings from the configured URL, or None if disabled."""
    url = settings.REDIS_URL
    if not url or not url.strip():
        return None
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    """ARQ worker settings — referenced by ``arq`` CLI and programmatic runner."""

    functions = [retrieval_job]
    redis_settings = _redis_settings()
    keep_result: int = 300
    keep_result_failed: int = 300
    max_retries: int = 0


async def enqueue_retrieval(
    execution_id: str,
    investigation_id: str,
    query: str,
    paper_limit: int = 10,
) -> str:
    """Enqueue a retrieval job and return the job ID."""
    pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        job = await pool.enqueue_job(
            "retrieval_job",
            execution_id,
            investigation_id,
            query,
            paper_limit,
        )
        logger.info(
            "retrieval_enqueued",
            job_id=job.job_id if job else None,
            execution_id=execution_id,
        )
        return job.job_id if job else ""
    finally:
        await pool.close()
