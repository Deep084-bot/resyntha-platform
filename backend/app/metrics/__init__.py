"""Application metrics — Prometheus-compatible counters, gauges, histograms.

Usage::

    from app.metrics import get_metrics_service

    metrics = get_metrics_service()
    metrics.http_requests_total.inc(method="GET", endpoint="/health", status="200")
"""

from app.metrics.middleware import MetricsMiddleware
from app.metrics.registry import Counter, Gauge, Histogram
from app.metrics.service import (
    MetricsService,
    get_metrics_service,
    reset_metrics_service,
)

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsMiddleware",
    "MetricsService",
    "get_metrics_service",
    "reset_metrics_service",
]
