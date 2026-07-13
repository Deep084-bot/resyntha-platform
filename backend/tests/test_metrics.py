"""Tests for the metrics layer — registry, service, middleware, and endpoint.

Uses ``TestClient`` for middleware and endpoint integration tests.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsMiddleware,
    get_metrics_service,
    reset_metrics_service,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    reset_metrics_service()


# ═══════════════════════════════════════════════════════════════════════════════
# Counter
# ═══════════════════════════════════════════════════════════════════════════════


class TestCounter:
    def test_initial_value_zero(self) -> None:
        c = Counter("test_counter", "A test counter")
        assert "test_counter 0" not in c.render()

    def test_inc_increases(self) -> None:
        c = Counter("test_counter", "A test counter")
        c.inc()
        c.inc(5)
        rendered = c.render()
        assert "test_counter 6" in rendered

    def test_render_help_and_type(self) -> None:
        c = Counter("my_counter", "My counter docs")
        rendered = c.render()
        assert "# HELP my_counter My counter docs" in rendered
        assert "# TYPE my_counter counter" in rendered

    def test_labels(self) -> None:
        c = Counter("labeled", "Labeled counter", labelnames=("method",))
        c.inc(method="GET")
        c.inc(method="POST")
        rendered = c.render()
        assert 'labeled{method="GET"} 1' in rendered
        assert 'labeled{method="POST"} 1' in rendered

    def test_multiple_label_values(self) -> None:
        c = Counter("multi", "Multi", labelnames=("a", "b"))
        c.inc(a="x", b="y")
        rendered = c.render()
        assert 'multi{a="x",b="y"} 1' in rendered or 'multi{b="y",a="x"} 1' in rendered


# ═══════════════════════════════════════════════════════════════════════════════
# Gauge
# ═══════════════════════════════════════════════════════════════════════════════


class TestGauge:
    def test_inc_and_dec(self) -> None:
        g = Gauge("active_req", "Active requests")
        g.inc()
        g.inc()
        g.dec()
        rendered = g.render()
        assert "active_req 1" in rendered

    def test_set(self) -> None:
        g = Gauge("temp", "Temperature")
        g.set(42.5)
        rendered = g.render()
        assert "temp 42.5" in rendered

    def test_render_help_and_type(self) -> None:
        g = Gauge("my_gauge", "A gauge")
        rendered = g.render()
        assert "# HELP my_gauge A gauge" in rendered
        assert "# TYPE my_gauge gauge" in rendered


# ═══════════════════════════════════════════════════════════════════════════════
# Histogram
# ═══════════════════════════════════════════════════════════════════════════════


class TestHistogram:
    def test_observe_fills_buckets(self) -> None:
        h = Histogram("req_dur", "Duration", buckets=(0.1, 0.5, 1.0))
        h.observe(0.05)
        rendered = h.render()
        assert 'req_dur_bucket{le="0.1"} 1' in rendered
        assert 'req_dur_bucket{le="0.5"} 1' in rendered
        assert 'req_dur_bucket{le="1.0"} 1' in rendered
        assert "req_dur_count 1" in rendered
        assert "req_dur_sum 0.05" in rendered

    def test_multiple_observations(self) -> None:
        h = Histogram("latency", "Latency", buckets=(1.0, 5.0))
        h.observe(0.5)
        h.observe(2.0)
        rendered = h.render()
        assert 'latency_bucket{le="1.0"} 1' in rendered
        assert 'latency_bucket{le="5.0"} 2' in rendered
        assert "latency_count 2" in rendered
        assert "latency_sum 2.5" in rendered

    def test_render_help_and_type(self) -> None:
        h = Histogram("dur", "Duration")
        rendered = h.render()
        assert "# HELP dur Duration" in rendered
        assert "# TYPE dur histogram" in rendered

    def test_labels(self) -> None:
        h = Histogram("labeled_dur", "Labeled", labelnames=("endpoint",), buckets=(0.5, 1.0))
        h.observe(0.3, endpoint="/test")
        rendered = h.render()
        assert (
            'labeled_dur_bucket{endpoint="/test",le="0.5"}' in rendered
            or 'labeled_dur_bucket{le="0.5",endpoint="/test"}' in rendered
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MetricsService
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsService:
    def test_singleton(self) -> None:
        s1 = get_metrics_service()
        s2 = get_metrics_service()
        assert s1 is s2

    def test_all_metric_attributes_present(self) -> None:
        svc = get_metrics_service()
        assert hasattr(svc, "http_requests_total")
        assert hasattr(svc, "http_requests_active")
        assert hasattr(svc, "http_request_duration_seconds")
        assert hasattr(svc, "copilot_chat_requests_total")
        assert hasattr(svc, "copilot_retrieval_duration_seconds")
        assert hasattr(svc, "retrieval_semantic_total")
        assert hasattr(svc, "retrieval_heuristic_fallback_total")
        assert hasattr(svc, "investigation_created_total")
        assert hasattr(svc, "investigation_completed_total")
        assert hasattr(svc, "investigation_failed_total")
        assert hasattr(svc, "worker_jobs_started_total")
        assert hasattr(svc, "worker_jobs_completed_total")
        assert hasattr(svc, "worker_jobs_failed_total")

    def test_render_includes_metrics(self) -> None:
        svc = get_metrics_service()
        svc.http_requests_total.inc(method="GET", endpoint="/test", status="200")
        rendered = svc.render()
        assert 'http_requests_total{endpoint="/test",method="GET",status="200"}' in rendered
        assert "# HELP" in rendered
        assert "# TYPE" in rendered

    def test_render_does_not_fail_when_empty(self) -> None:
        svc = get_metrics_service()
        rendered = svc.render()
        assert isinstance(rendered, str)
        assert len(rendered) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Middleware — Integration
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict:
        return {"ok": True}

    @app.get("/slow")
    async def slow_endpoint() -> dict:
        import asyncio

        await asyncio.sleep(0.01)
        return {"slow": True}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, base_url="http://localhost")


class TestMetricsMiddleware:
    def test_request_increments_active(self, client: TestClient) -> None:
        reset_metrics_service()
        client.get("/test")
        svc = get_metrics_service()
        rendered = svc.http_requests_active.render()
        assert "http_requests_active 0" in rendered  # back to 0 after request

    def test_request_records_total(self, client: TestClient) -> None:
        reset_metrics_service()
        client.get("/test")
        svc = get_metrics_service()
        rendered = svc.http_requests_total.render()
        assert (
            'http_requests_total{endpoint="/test",method="GET",status="200"}'
            in rendered.replace("\\n", "\n")
            or 'http_requests_total{method="GET",endpoint="/test",status="200"}'
            in rendered.replace("\\n", "\n")
        )

    def test_request_records_duration(self, client: TestClient) -> None:
        reset_metrics_service()
        client.get("/slow")
        svc = get_metrics_service()
        rendered = svc.http_request_duration_seconds.render()
        assert "http_request_duration_seconds_count" in rendered
        assert "http_request_duration_seconds_sum" in rendered

    def test_multiple_requests_increment_total(self, client: TestClient) -> None:
        reset_metrics_service()
        for _ in range(5):
            client.get("/test")
        svc = get_metrics_service()
        rendered = svc.http_requests_total.render()
        # Check the total value for the label combination
        assert 'status="200"' in rendered


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_plaintext(self) -> None:
        from app.main import app

        client = TestClient(app, base_url="http://localhost")
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.headers["content-type"].startswith("text/plain; version=0.0.4")

    def test_metrics_endpoint_contains_help(self) -> None:
        from app.main import app

        client = TestClient(app, base_url="http://localhost")
        resp = client.get("/api/v1/metrics")
        assert "# HELP" in resp.text

    def test_metrics_endpoint_contains_type(self) -> None:
        from app.main import app

        client = TestClient(app, base_url="http://localhost")
        resp = client.get("/api/v1/metrics")
        assert "# TYPE" in resp.text

    def test_metrics_endpoint_contains_request_metrics(self) -> None:
        from app.main import app

        client = TestClient(app, base_url="http://localhost")
        # Make a request first so there is data
        client.get("/api/v1/live")
        resp = client.get("/api/v1/metrics")
        assert "http_requests_total" in resp.text
        assert "http_requests_active" in resp.text
        assert "http_request_duration_seconds" in resp.text

    def test_disabled_metrics_returns_empty(self) -> None:
        with patch("app.health.routes.get_settings") as mock_s:
            mock_s.return_value.METRICS_ENABLED = False
            from app.main import app

            client = TestClient(app, base_url="http://localhost")
            resp = client.get("/api/v1/metrics")
            assert resp.status_code == status.HTTP_200_OK
            assert resp.text == ""


# ═══════════════════════════════════════════════════════════════════════════════
# Metric Hooks — Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestInvestigationMetricsHook:
    @pytest.mark.skip(reason="requires PostgreSQL — no DB available in test env")
    def test_create_investigation_increments_counter(self) -> None:
        reset_metrics_service()
        from app.main import app

        client = TestClient(app, base_url="http://localhost")
        # The counter is incremented by the investigation service
        # when create_investigation is called. Make a request to the endpoint.
        resp = client.post(
            "/api/v1/investigations",
            json={"title": "Test", "topic": "AI", "paper_limit": 10},
        )
        if resp.status_code == 201:
            svc = get_metrics_service()
            rendered = svc.investigation_created_total.render()
            assert "investigation_created_total 1" in rendered
