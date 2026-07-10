"""Tests for the rate limiting layer — backends, service, middleware, decorators.

Uses a mock Redis for backend tests and ``TestClient`` for middleware
integration tests.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.rate_limit import (
    InMemoryBackend,
    RateLimitMiddleware,
    RateLimitService,
    RedisBackend,
    rate_limit,
)
from app.rate_limit.middleware import RATE_LIMIT_ATTR, _override_registry


def _run(coro):
    return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# InMemoryBackend
# ═══════════════════════════════════════════════════════════════════════════════


class TestInMemoryBackend:
    def test_allows_within_limit(self) -> None:
        backend = InMemoryBackend()
        r = _run(backend.check("client:1", limit=5, window=60))
        assert r.allowed
        assert r.remaining == 4

    def test_blocks_when_exceeded(self) -> None:
        backend = InMemoryBackend()
        for _ in range(3):
            _run(backend.check("client:2", limit=3, window=60))
        r = _run(backend.check("client:2", limit=3, window=60))
        assert not r.allowed
        assert r.remaining == 0

    def test_window_reset(self) -> None:
        backend = InMemoryBackend()
        short_window = 1
        for _ in range(2):
            _run(backend.check("client:3", limit=2, window=short_window))
        r = _run(backend.check("client:3", limit=2, window=short_window))
        assert not r.allowed
        time.sleep(1.1)
        r = _run(backend.check("client:3", limit=2, window=short_window))
        assert r.allowed

    def test_isolates_clients(self) -> None:
        backend = InMemoryBackend()
        for _ in range(3):
            _run(backend.check("client:a", limit=3, window=60))
        r_a = _run(backend.check("client:a", limit=3, window=60))
        assert not r_a.allowed
        r_b = _run(backend.check("client:b", limit=3, window=60))
        assert r_b.allowed

    def test_remaining_decreases(self) -> None:
        backend = InMemoryBackend()
        r1 = _run(backend.check("client:4", limit=5, window=60))
        assert r1.remaining == 4
        r2 = _run(backend.check("client:4", limit=5, window=60))
        assert r2.remaining == 3

    def test_retry_after_on_block(self) -> None:
        backend = InMemoryBackend()
        for _ in range(2):
            _run(backend.check("client:5", limit=2, window=10))
        r = _run(backend.check("client:5", limit=2, window=10))
        assert not r.allowed
        assert 0 < r.retry_after <= 10


# ═══════════════════════════════════════════════════════════════════════════════
# RedisBackend
# ═══════════════════════════════════════════════════════════════════════════════


class TestRedisBackend:
    def test_allows_within_limit(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        backend = RedisBackend(redis=mock_redis)
        r = _run(backend.check("client:1", limit=5, window=60))
        assert r.allowed
        assert r.remaining == 4

    def test_blocks_when_exceeded(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 6
        mock_redis.expire.return_value = True
        backend = RedisBackend(redis=mock_redis)
        r = _run(backend.check("client:2", limit=5, window=60))
        assert not r.allowed
        assert r.remaining == 0

    def test_falls_back_to_memory_on_redis_error(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr.side_effect = ConnectionError("down")
        backend = RedisBackend(redis=mock_redis)
        r = _run(backend.check("client:3", limit=5, window=60))
        assert r.allowed

    def test_falls_back_when_redis_none(self) -> None:
        with patch("app.rate_limit.service.get_redis", return_value=None):
            backend = RedisBackend(redis=None)
            r = _run(backend.check("client:4", limit=5, window=60))
            assert r.allowed

    def test_sets_expire_on_first_incr(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        backend = RedisBackend(redis=mock_redis)
        _run(backend.check("client:5", limit=10, window=60))
        mock_redis.expire.assert_awaited_once()

    def test_does_not_set_expire_on_subsequent(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 2
        mock_redis.expire.return_value = True
        backend = RedisBackend(redis=mock_redis)
        _run(backend.check("client:6", limit=10, window=60))
        mock_redis.expire.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# RateLimitService
# ═══════════════════════════════════════════════════════════════════════════════


class TestRateLimitService:
    def test_disabled_allows_all(self) -> None:
        with patch("app.rate_limit.service.get_settings") as mock_s:
            mock_s.return_value.RATE_LIMIT_ENABLED = False
            mock_s.return_value.RATE_LIMIT_BACKEND = "memory"
            svc = RateLimitService(backend="memory")
            r = _run(svc.check("key", limit=1, window=60))
            assert r.allowed

    def test_memory_backend_via_service(self) -> None:
        svc = RateLimitService(backend="memory")
        r1 = _run(svc.check("key", limit=2, window=60))
        assert r1.allowed
        r2 = _run(svc.check("key", limit=2, window=60))
        assert r2.allowed
        r3 = _run(svc.check("key", limit=2, window=60))
        assert not r3.allowed


# ═══════════════════════════════════════════════════════════════════════════════
# Decorator
# ═══════════════════════════════════════════════════════════════════════════════


class TestRateLimitDecorator:
    def test_sets_attribute_on_function(self) -> None:
        @rate_limit(limit=50, window=30)
        async def my_handler() -> dict:
            return {"ok": True}

        assert hasattr(my_handler, RATE_LIMIT_ATTR)
        cfg = getattr(my_handler, RATE_LIMIT_ATTR)
        assert cfg == {"limit": 50, "window": 30}

    def test_registers_in_global_registry(self) -> None:
        _override_registry.clear()
        rate_limit("POST", "/api/v1/test", limit=10, window=10)

        key = ("POST", "/api/v1/test")
        assert key in _override_registry
        assert _override_registry[key] == {"limit": 10, "window": 10}
        _override_registry.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# Middleware — Integration
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/api/v1/live")
    async def live() -> dict:
        return {"status": "ok"}

    @app.get("/api/v1/general")
    async def general() -> dict:
        return {"data": "general"}

    @app.get("/api/v1/override")
    @rate_limit("GET", "/api/v1/override", limit=3, window=60)
    async def override_endpoint() -> dict:
        return {"overridden": True}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, base_url="http://localhost")


class TestRateLimitMiddleware:
    def test_unlimited_path(self, client: TestClient) -> None:
        for _ in range(10):
            resp = client.get("/api/v1/live")
            assert resp.status_code == status.HTTP_200_OK

    def response_has_rate_limit_headers(self, client: TestClient) -> None:
        resp = client.get("/api/v1/general")
        assert resp.status_code == status.HTTP_200_OK
        assert "x-ratelimit-limit" in resp.headers
        assert "x-ratelimit-remaining" in resp.headers
        assert "x-ratelimit-reset" in resp.headers

    def test_override_endpoint(self, client: TestClient) -> None:
        for _ in range(3):
            resp = client.get("/api/v1/override")
            assert resp.status_code == status.HTTP_200_OK
        resp = client.get("/api/v1/override")
        assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_429_headers(self, client: TestClient) -> None:
        for _ in range(3):
            client.get("/api/v1/override")
        resp = client.get("/api/v1/override")
        assert resp.headers["x-ratelimit-limit"] == "3"
        assert resp.headers["x-ratelimit-remaining"] == "0"
        assert "retry-after" in resp.headers
        assert int(resp.headers["retry-after"]) > 0

    def test_429_body(self, client: TestClient) -> None:
        for _ in range(3):
            client.get("/api/v1/override")
        resp = client.get("/api/v1/override")
        body = resp.json()
        assert body["status"] == 429
        assert "title" in body
        assert "detail" in body

    def test_remaining_decreases(self, client: TestClient) -> None:
        r1 = int(client.get("/api/v1/general").headers["x-ratelimit-remaining"])
        r2 = int(client.get("/api/v1/general").headers["x-ratelimit-remaining"])
        assert r2 < r1

    def test_disabled_rate_limiting(self) -> None:
        app = FastAPI()
        with patch("app.rate_limit.service.get_settings") as mock_svc:
            mock_svc.return_value.RATE_LIMIT_ENABLED = False
            mock_svc.return_value.RATE_LIMIT_BACKEND = "memory"
            app.add_middleware(RateLimitMiddleware)

            @app.get("/test")
            async def endpoint() -> dict:
                return {"ok": True}

            c = TestClient(app, base_url="http://localhost")
            for _ in range(200):
                resp = c.get("/test")
                assert resp.status_code == status.HTTP_200_OK
