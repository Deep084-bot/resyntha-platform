"""Typed response models for health-check endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    """Health status of a single dependency."""

    status: str = Field(description="health | unhealthy | configured | disabled")
    reason: str | None = Field(None, description="human-readable explanation when unhealthy")


class HealthResponse(BaseModel):
    """Overall application health."""

    application: str
    version: str
    environment: str
    uptime: str
    status: str = "healthy"


class LivenessResponse(BaseModel):
    """Simple liveness probe response."""

    status: str = "alive"


class ReadinessResponse(BaseModel):
    """Readiness probe response with per-component status."""

    status: str = "ready"
    components: dict[str, ComponentHealth]


class MetricsInfoResponse(BaseModel):
    """Static runtime information."""

    application: str
    version: str
    git_commit: str
    build_time: str
    python_version: str
    environment: str
    debug: bool
