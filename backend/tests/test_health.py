"""Tests for health-check and runtime-diagnostics endpoints.

Uses ``TestClient`` against the full FastAPI application so that
middleware, routing, and response serialisation are exercised end
to end.  Dependencies are mocked to avoid external services.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.health.models import (
    ComponentHealth,
    HealthResponse,
    LivenessResponse,
    MetricsInfoResponse,
    ReadinessResponse,
)
from app.health.service import get_uptime, record_startup_time


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app, base_url="http://localhost")


class TestLiveness:
    def test_returns_alive(self, client: TestClient) -> None:
        resp = client.get("/api/v1/live")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {"status": "alive"}

    def test_response_schema(self) -> None:
        model = LivenessResponse()
        assert model.status == "alive"


class TestHealth:
    def test_returns_healthy(self, client: TestClient) -> None:
        resp = client.get("/api/v1/health")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["application"] == "resyntha"
        assert body["version"] == "0.1.0"
        assert body["environment"] in ("development", "testing", "production")
        assert "uptime" in body

    def test_uptime_is_non_empty_string(self) -> None:
        uptime = get_uptime()
        assert isinstance(uptime, str)
        assert len(uptime) > 0

    def test_uptime_format(self) -> None:
        record_startup_time()
        uptime = get_uptime()
        assert "s" in uptime  # should always contain seconds

    def test_response_schema(self) -> None:
        model = HealthResponse(
            application="test",
            version="1.0",
            environment="testing",
            uptime="10s",
            status="healthy",
        )
        assert model.application == "test"


class TestMetricsInfo:
    def test_returns_runtime_info(self, client: TestClient) -> None:
        resp = client.get("/api/v1/metrics/info")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["application"] == "resyntha"
        assert body["version"] == "0.1.0"
        assert "git_commit" in body
        assert "build_time" in body
        assert "python_version" in body
        assert "environment" in body
        assert "debug" in body

    def test_response_schema(self) -> None:
        model = MetricsInfoResponse(
            application="test",
            version="1.0",
            git_commit="abc123",
            build_time="2026-01-01T00:00:00",
            python_version="3.14",
            environment="testing",
            debug=False,
        )
        assert model.git_commit == "abc123"


class TestReadiness:
    def test_ready_success(self, client: TestClient) -> None:
        with (
            patch("app.health.service._check_db", return_value=True),
            patch("app.health.service._check_redis", AsyncMock(return_value=True)),
        ):
            resp = client.get("/api/v1/ready")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "ready"
        components = body["components"]
        assert "database" in components
        assert "redis" in components
        assert "llm" in components
        assert "embedding" in components
        assert "worker" in components

    def test_ready_database_failure(self, client: TestClient) -> None:
        with patch("app.health.service._check_db", return_value=False):
            resp = client.get("/api/v1/ready")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        body = resp.json()
        assert body["status"] == "not_ready"
        assert body["components"]["database"]["status"] == "unhealthy"

    def test_ready_redis_failure(self, client: TestClient) -> None:
        with patch("app.health.service._check_redis", AsyncMock(return_value=False)):
            resp = client.get("/api/v1/ready")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        body = resp.json()
        assert body["status"] == "not_ready"
        assert body["components"]["redis"]["status"] == "unhealthy"

    def test_ready_database_exception(self, client: TestClient) -> None:
        with patch("app.health.service._check_db", side_effect=Exception("db error")):
            resp = client.get("/api/v1/ready")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        body = resp.json()
        assert body["components"]["database"]["status"] == "unhealthy"

    def test_ready_no_stack_trace_leak(self, client: TestClient) -> None:
        with patch("app.health.service._check_db", side_effect=Exception("internal details")):
            resp = client.get("/api/v1/ready")
        body = resp.json()
        # The reason should not contain the full traceback — just the error message
        reason = body["components"]["database"].get("reason", "")
        assert "Traceback" not in reason

    def test_response_schema(self) -> None:
        model = ReadinessResponse(
            status="ready",
            components={
                "database": ComponentHealth(status="healthy"),
                "redis": ComponentHealth(status="unhealthy", reason="timeout"),
            },
        )
        assert model.status == "ready"
        assert model.components["redis"].reason == "timeout"

    def test_llm_configured_is_considered_healthy(self, client: TestClient) -> None:
        with (
            patch("app.health.service._check_db", return_value=True),
            patch("app.health.service._check_redis", AsyncMock(return_value=True)),
        ):
            resp = client.get("/api/v1/ready")
        assert resp.status_code == status.HTTP_200_OK
        llm_status = resp.json()["components"]["llm"]["status"]
        assert llm_status in ("healthy", "configured")


class TestComponentHealth:
    def test_default_reason_is_none(self) -> None:
        ch = ComponentHealth(status="healthy")
        assert ch.reason is None

    def test_with_reason(self) -> None:
        ch = ComponentHealth(status="unhealthy", reason="ping failed")
        assert ch.reason == "ping failed"
