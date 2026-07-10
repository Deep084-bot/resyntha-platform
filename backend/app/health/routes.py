"""Health-check, runtime-diagnostics, and metrics HTTP endpoints.

Provided under the ``/api/v1`` prefix:
  - ``GET /health``           — overall application health
  - ``GET /live``             — liveness probe (no deps)
  - ``GET /ready``            — readiness probe (all deps)
  - ``GET /metrics/info``     — static runtime information
  - ``GET /metrics``          — Prometheus-compatible metrics
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.config import BUILD_TIME, GIT_COMMIT, PYTHON_VERSION, get_settings
from app.metrics import get_metrics_service
from app.observability.logger import get_logger

from . import service as health_service
from .models import (
    HealthResponse,
    LivenessResponse,
    MetricsInfoResponse,
    ReadinessResponse,
)

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return overall application health."""
    settings = get_settings()
    return HealthResponse(
        application=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        uptime=health_service.get_uptime(),
        status="healthy",
    )


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Return a simple liveness indication.

    This endpoint performs no dependency checks and is suitable for
    platform-level liveness probes.
    """
    return LivenessResponse()


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    """Return readiness status for all application dependencies.

    Checks database, Redis, LLM configuration, embedding provider,
    and worker connectivity.  Returns HTTP 200 when all required
    dependencies are healthy, HTTP 503 otherwise.
    """
    db_health = await health_service.check_database()
    redis_health = await health_service.check_redis()
    llm_health = await health_service.check_llm()
    embedding_health = await health_service.check_embedding_provider()
    worker_health = await health_service.check_worker()

    components = {
        "database": db_health,
        "redis": redis_health,
        "llm": llm_health,
        "embedding": embedding_health,
        "worker": worker_health,
    }

    all_healthy = all(
        comp.status == "healthy"
        or (comp.status == "configured" and name in ("llm",))
        or (comp.status == "disabled" and name in ("worker",))
        for name, comp in components.items()
    )

    if all_healthy:
        return ReadinessResponse(status="ready", components=components)

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    for name, comp in components.items():
        if comp.status != "healthy" and not (
            comp.status == "configured" and name == "llm"
        ) and not (comp.status == "disabled" and name == "worker"):
            logger.warning(
                "readiness_failure",
                component=name,
                status=comp.status,
                reason=comp.reason,
            )

    return ReadinessResponse(status="not_ready", components=components)


@router.get("/metrics/info", response_model=MetricsInfoResponse)
async def metrics_info() -> MetricsInfoResponse:
    """Return static runtime information about the application."""
    settings = get_settings()
    return MetricsInfoResponse(
        application=settings.APP_NAME,
        version=settings.APP_VERSION,
        git_commit=GIT_COMMIT,
        build_time=BUILD_TIME,
        python_version=PYTHON_VERSION,
        environment=settings.ENVIRONMENT.value,
        debug=settings.DEBUG,
    )


@router.get("/metrics")
async def metrics() -> Response:
    """Return Prometheus-compatible metrics.

    When ``METRICS_ENABLED`` is ``False`` the response body will be
    empty (all zero-initialised metrics are still rendered because
    the registry always exists).
    """
    settings = get_settings()
    if not settings.METRICS_ENABLED:
        return Response(
            content="",
            media_type="text/plain; version=0.0.4",
            status_code=status.HTTP_200_OK,
        )
    svc = get_metrics_service()
    return Response(
        content=svc.render(),
        media_type="text/plain; version=0.0.4",
    )
