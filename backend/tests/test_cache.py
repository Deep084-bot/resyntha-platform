"""Tests for the caching layer — CacheService, cache keys, and decorators.

Uses mocked Redis so all tests run without a real Redis server.
Async cache operations are driven via ``asyncio.run()``.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pydantic
import pytest

from app.cache import CacheService, cached, invalidate, invalidate_investigation
from app.cache.keys import (
    all_investigation_pattern,
    gap_report_key,
    graph_key,
    investigation_key,
    knowledge_package_key,
    landscape_key,
    retrieval_key,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex = AsyncMock()
    redis.delete = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    redis.exists = AsyncMock(return_value=0)
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def cache_service(mock_redis: AsyncMock) -> CacheService:
    return CacheService(redis=mock_redis)


def _run(coro):
    return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# Cache Keys
# ═══════════════════════════════════════════════════════════════════════════════


class TestCacheKeys:
    def test_investigation_key(self) -> None:
        inv_id = uuid.uuid4()
        assert investigation_key(inv_id) == f"investigation:{inv_id}"

    def test_graph_key(self) -> None:
        inv_id = uuid.uuid4()
        assert graph_key(inv_id) == f"graph:{inv_id}"

    def test_landscape_key(self) -> None:
        inv_id = uuid.uuid4()
        assert landscape_key(inv_id) == f"landscape:{inv_id}"

    def test_gap_report_key(self) -> None:
        inv_id = uuid.uuid4()
        assert gap_report_key(inv_id) == f"gap_report:{inv_id}"

    def test_knowledge_package_key(self) -> None:
        inv_id = uuid.uuid4()
        assert knowledge_package_key(inv_id) == f"knowledge_package:{inv_id}"

    def test_retrieval_key_format(self) -> None:
        inv_id = uuid.uuid4()
        key = retrieval_key(inv_id, "what is transformer?")
        assert key.startswith(f"retrieval:{inv_id}:")
        assert len(key) == len(f"retrieval:{inv_id}:") + 16

    def test_retrieval_key_deterministic(self) -> None:
        inv_id = uuid.uuid4()
        q = "same question"
        assert retrieval_key(inv_id, q) == retrieval_key(inv_id, q)

    def test_retrieval_key_different_inputs(self) -> None:
        inv_id = uuid.uuid4()
        assert retrieval_key(inv_id, "q1") != retrieval_key(inv_id, "q2")

    def test_all_investigation_pattern(self) -> None:
        inv_id = uuid.uuid4()
        assert all_investigation_pattern(inv_id) == f"*:{inv_id}"


# ═══════════════════════════════════════════════════════════════════════════════
# CacheService — Core operations
# ═══════════════════════════════════════════════════════════════════════════════


class TestCacheService:
    def test_set_and_get(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = json.dumps({"hello": "world"})
        assert _run(cache_service.set("my_key", {"hello": "world"}, ttl=60))
        value = _run(cache_service.get("my_key"))
        assert value == {"hello": "world"}

    def test_get_miss(self, cache_service: CacheService) -> None:
        assert _run(cache_service.get("nonexistent")) is None

    def test_delete_existing(self, cache_service: CacheService) -> None:
        assert _run(cache_service.delete("key")) is True

    def test_delete_nonexistent(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.delete.return_value = 0
        assert _run(cache_service.delete("nonexistent")) is True  # idempotent

    def test_exists_true(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.exists.return_value = 1
        assert _run(cache_service.exists("key")) is True

    def test_exists_false(self, cache_service: CacheService) -> None:
        assert _run(cache_service.exists("key")) is False

    def test_ping_success(self, cache_service: CacheService) -> None:
        assert _run(cache_service.ping()) is True

    def test_ping_failure(self, mock_redis: AsyncMock) -> None:
        mock_redis.ping.side_effect = ConnectionError("down")
        svc = CacheService(redis=mock_redis)
        assert _run(svc.ping()) is False

    # ── delete_pattern ──────────────────────────────────────────────

    def test_delete_pattern(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.scan.return_value = (0, ["k1", "k2"])
        mock_redis.delete.return_value = 2
        count = _run(cache_service.delete_pattern("*:test"))
        assert count == 2
        mock_redis.delete.assert_awaited_with("k1", "k2")

    def test_delete_pattern_no_matches(self, cache_service: CacheService) -> None:
        assert _run(cache_service.delete_pattern("*:nonexistent")) == 0

    def test_delete_pattern_paginates(
        self, cache_service: CacheService, mock_redis: AsyncMock
    ) -> None:
        mock_redis.scan.side_effect = [
            (5, ["k1"]),
            (0, ["k2"]),
        ]
        mock_redis.delete.return_value = 2
        count = _run(cache_service.delete_pattern("*:test"))
        assert count == 2

    # ── get_or_compute ──────────────────────────────────────────────

    def test_get_or_compute_hit(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = json.dumps("cached_value")
        value, from_cache = _run(
            cache_service.get_or_compute(
                "key",
                fallback=AsyncMock(return_value="fresh_value"),
                ttl=60,
            )
        )
        assert value == "cached_value"
        assert from_cache is True

    def test_get_or_compute_miss(self, cache_service: CacheService) -> None:
        value, from_cache = _run(
            cache_service.get_or_compute(
                "key",
                fallback=AsyncMock(return_value="fresh_value"),
                ttl=60,
            )
        )
        assert value == "fresh_value"
        assert from_cache is False

    # ── Pydantic serialization ──────────────────────────────────────

    def test_set_pydantic_model(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        class DummyModel(pydantic.BaseModel):
            name: str
            count: int

        model = DummyModel(name="test", count=42)
        _run(cache_service.set("model_key", model, ttl=60))
        call_args = mock_redis.setex.call_args
        assert call_args is not None
        stored = json.loads(call_args[0][2])
        assert stored == {"name": "test", "count": 42}

    # ── Graceful degradation ────────────────────────────────────────

    def test_get_redis_unavailable(self) -> None:
        svc = CacheService(redis=None)
        with patch("app.cache.service.get_redis", return_value=None):
            assert _run(svc.get("key")) is None

    def test_set_redis_exception(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.setex.side_effect = ConnectionError("down")
        assert _run(cache_service.set("k", "v", ttl=60)) is False

    def test_get_redis_exception(self, cache_service: CacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.side_effect = ConnectionError("down")
        assert _run(cache_service.get("k")) is None

    def test_delete_redis_exception(
        self, cache_service: CacheService, mock_redis: AsyncMock
    ) -> None:
        mock_redis.delete.side_effect = ConnectionError("down")
        assert _run(cache_service.delete("k")) is False

    def test_delete_pattern_redis_exception(
        self, cache_service: CacheService, mock_redis: AsyncMock
    ) -> None:
        mock_redis.scan.side_effect = ConnectionError("down")
        assert _run(cache_service.delete_pattern("*:test")) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Decorators — @cached
# ═══════════════════════════════════════════════════════════════════════════════


class TestCachedDecorator:
    def test_cache_hit(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = json.dumps({"cached": "data"})
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @cached("test_key", ttl=60)
            async def my_func() -> dict:
                return {"cached": "fresh"}

            result = _run(my_func())
            assert result == {"cached": "data"}

    def test_cache_miss_computes_and_stores(self, mock_redis: AsyncMock) -> None:
        svc = CacheService(redis=mock_redis)
        call_count = 0

        with patch("app.cache.decorators._cache", return_value=svc):

            @cached("compute_key", ttl=60)
            async def compute() -> str:
                nonlocal call_count
                call_count += 1
                return f"result_{call_count}"

            r1 = _run(compute())
            assert r1 == "result_1"
            assert call_count == 1

            mock_redis.get.return_value = json.dumps("result_1")

            r2 = _run(compute())
            assert r2 == "result_1"
            assert call_count == 1  # not called again

    def test_key_format_with_kwargs(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = json.dumps("cached_value")
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @cached("{prefix}:{suffix}", ttl=60)
            async def lookup(*, prefix: str, suffix: str) -> str:
                return "fresh"

            result = _run(lookup(prefix="hello", suffix="world"))
            assert result == "cached_value"
            mock_redis.get.assert_awaited_with("hello:world")

    def test_cache_disabled(self) -> None:
        call_count = 0

        with (
            patch("app.cache.decorators._cache", return_value=CacheService(redis=None)),
        ):

            @cached("any_key", ttl=60)
            async def my_func() -> str:
                nonlocal call_count
                call_count += 1
                return "fresh"

            r1 = _run(my_func())
            assert r1 == "fresh"
            r2 = _run(my_func())
            assert r2 == "fresh"
            assert call_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Decorators — @invalidate
# ═══════════════════════════════════════════════════════════════════════════════


class TestInvalidateDecorator:
    def test_invalidate_single_key(self, mock_redis: AsyncMock) -> None:
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @invalidate("my_key")
            async def update() -> str:
                return "done"

            result = _run(update())
            assert result == "done"
            mock_redis.delete.assert_awaited_with("my_key")

    def test_invalidate_multiple_keys(self, mock_redis: AsyncMock) -> None:
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @invalidate("key_a", "key_b")
            async def update() -> str:
                return "done"

            _run(update())
            assert mock_redis.delete.call_count == 2
            mock_redis.delete.assert_any_await("key_a")
            mock_redis.delete.assert_any_await("key_b")

    def test_invalidate_with_format(self, mock_redis: AsyncMock) -> None:
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @invalidate("graph:{inv_id}", "landscape:{inv_id}")
            async def rerun(*, inv_id: str) -> str:
                return "done"

            _run(rerun(inv_id="abc-123"))
            mock_redis.delete.assert_any_await("graph:abc-123")
            mock_redis.delete.assert_any_await("landscape:abc-123")


# ═══════════════════════════════════════════════════════════════════════════════
# Decorators — @invalidate_investigation
# ═══════════════════════════════════════════════════════════════════════════════


class TestInvalidateInvestigationDecorator:
    def test_invalidates_pattern(self, mock_redis: AsyncMock) -> None:
        mock_redis.scan.return_value = (0, ["graph:id", "landscape:id"])
        mock_redis.delete.return_value = 2
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @invalidate_investigation()
            async def rerun(*, investigation_id: str) -> str:
                return "done"

            result = _run(rerun(investigation_id="id"))
            assert result == "done"
            mock_redis.delete.assert_awaited_with("graph:id", "landscape:id")

    def test_no_scan_when_id_missing(self, mock_redis: AsyncMock) -> None:
        svc = CacheService(redis=mock_redis)

        with patch("app.cache.decorators._cache", return_value=svc):

            @invalidate_investigation()
            async def rerun() -> str:
                return "done"

            _run(rerun())
            mock_redis.scan.assert_not_called()
