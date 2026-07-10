"""MetricsService — singleton that owns all metric instances.

Provides a single ``get_metrics_service()`` entry point and exposes
named metric objects for collectors and middleware to update.
"""

from __future__ import annotations

from app.config import get_settings
from app.metrics.registry import Counter, Gauge, Histogram


class MetricsService:
    """Application metrics registry.

    All metric objects live here.  Middleware and collectors reference
    ``metrics_service.some_counter.inc()`` etc.
    """

    def __init__(self) -> None:
        settings = get_settings()
        namespace = settings.METRICS_NAMESPACE
        subsystem = settings.METRICS_SUBSYSTEM
        p = f"{namespace}_{subsystem}"  # resyntha_backend

        # ── Request metrics ───────────────────────────────────────────
        self.http_requests_total = Counter(
            f"{p}_http_requests_total",
            "Total HTTP requests",
            labelnames=("method", "endpoint", "status"),
        )
        self.http_requests_active = Gauge(
            f"{p}_http_requests_active",
            "Currently active HTTP requests",
        )
        self.http_request_duration_seconds = Histogram(
            f"{p}_http_request_duration_seconds",
            "HTTP request latency (seconds)",
            labelnames=("method", "endpoint"),
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        # ── Copilot metrics ───────────────────────────────────────────
        self.copilot_chat_requests_total = Counter(
            f"{p}_copilot_chat_requests_total",
            "Total copilot chat requests",
        )
        self.copilot_stream_requests_total = Counter(
            f"{p}_copilot_stream_requests_total",
            "Total copilot streaming chat requests",
        )
        self.copilot_retrieval_duration_seconds = Histogram(
            f"{p}_copilot_retrieval_duration_seconds",
            "Copilot retrieval duration (seconds)",
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
        )
        self.copilot_llm_duration_seconds = Histogram(
            f"{p}_copilot_llm_duration_seconds",
            "Copilot LLM generation duration (seconds)",
            buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        )
        self.copilot_prompt_generation_duration_seconds = Histogram(
            f"{p}_copilot_prompt_generation_duration_seconds",
            "Copilot prompt generation duration (seconds)",
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5),
        )
        self.copilot_total_answer_duration_seconds = Histogram(
            f"{p}_copilot_total_answer_duration_seconds",
            "Copilot total answer duration (seconds)",
            buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
        )

        # ── Retrieval metrics ─────────────────────────────────────────
        self.retrieval_semantic_total = Counter(
            f"{p}_retrieval_semantic_total",
            "Total semantic retrieval calls",
        )
        self.retrieval_heuristic_fallback_total = Counter(
            f"{p}_retrieval_heuristic_fallback_total",
            "Total heuristic fallback retrieval calls",
        )
        self.retrieval_cache_hits_total = Counter(
            f"{p}_retrieval_cache_hits_total",
            "Total retrieval cache hits",
        )
        self.retrieval_cache_misses_total = Counter(
            f"{p}_retrieval_cache_misses_total",
            "Total retrieval cache misses",
        )
        self.retrieval_failures_total = Counter(
            f"{p}_retrieval_failures_total",
            "Total retrieval failures",
        )
        self.retrieval_average_sections = Gauge(
            f"{p}_retrieval_average_sections",
            "Average number of retrieved sections",
        )
        self.retrieval_prompt_size = Histogram(
            f"{p}_retrieval_prompt_size",
            "Retrieval prompt size in characters",
            buckets=(100, 500, 1000, 2500, 5000, 10000, 25000),
        )

        # ── Investigation metrics ──────────────────────────────────────
        self.investigation_created_total = Counter(
            f"{p}_investigation_created_total",
            "Total investigations created",
        )
        self.investigation_completed_total = Counter(
            f"{p}_investigation_completed_total",
            "Total investigations completed",
        )
        self.investigation_failed_total = Counter(
            f"{p}_investigation_failed_total",
            "Total investigations failed",
        )
        self.investigation_pipeline_duration_seconds = Histogram(
            f"{p}_investigation_pipeline_duration_seconds",
            "Investigation pipeline duration (seconds)",
            buckets=(10, 30, 60, 120, 300, 600),
        )

        # ── Worker metrics ─────────────────────────────────────────────
        self.worker_jobs_started_total = Counter(
            f"{p}_worker_jobs_started_total",
            "Total worker jobs started",
        )
        self.worker_jobs_completed_total = Counter(
            f"{p}_worker_jobs_completed_total",
            "Total worker jobs completed",
        )
        self.worker_jobs_failed_total = Counter(
            f"{p}_worker_jobs_failed_total",
            "Total worker jobs failed",
        )
        self.worker_stage_duration_seconds = Histogram(
            f"{p}_worker_stage_duration_seconds",
            "Worker stage duration (seconds)",
            labelnames=("stage",),
            buckets=(1, 5, 10, 30, 60, 120, 300),
        )
        self.worker_embedding_duration_seconds = Histogram(
            f"{p}_worker_embedding_duration_seconds",
            "Embedding generation duration (seconds)",
            buckets=(1, 5, 10, 30, 60, 120),
        )
        self.worker_cache_invalidations_total = Counter(
            f"{p}_worker_cache_invalidations_total",
            "Total cache invalidations by workers",
        )

        # ── Cache metrics ──────────────────────────────────────────────
        self.cache_hits_total = Counter(
            f"{p}_cache_hits_total",
            "Total cache hits",
            labelnames=("key",),
        )
        self.cache_misses_total = Counter(
            f"{p}_cache_misses_total",
            "Total cache misses",
            labelnames=("key",),
        )

    # ── Render ─────────────────────────────────────────────────────────

    def render(self) -> str:
        """Return all metrics as Prometheus exposition-format text."""
        from app.metrics.registry import Counter, Gauge, Histogram

        parts: list[str] = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, (Counter, Gauge, Histogram)):
                parts.append(attr.render())
        return "\n".join(parts)


# ── Singleton ─────────────────────────────────────────────────────────────────

_metrics_service: MetricsService | None = None


def get_metrics_service() -> MetricsService:
    global _metrics_service  # noqa: PLW0603
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service


def reset_metrics_service() -> None:
    """Reset the singleton (used in tests)."""
    global _metrics_service  # noqa: PLW0603
    _metrics_service = None
