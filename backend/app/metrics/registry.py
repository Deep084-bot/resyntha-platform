"""Lightweight Prometheus-compatible metric primitives.

Each metric type implements ``render()`` which returns the
Prometheus exposition-format string for that metric.
"""

from __future__ import annotations

import threading
from collections import defaultdict


def _sanitize(name: str) -> str:
    return name.replace("-", "_").replace(".", "_").replace(" ", "_")


def _label_str(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
    return "{" + ",".join(parts) + "}"


# ── Counter ───────────────────────────────────────────────────────────────────


class Counter:
    """A monotonically-increasing counter.

    Thread-safe via a lock.
    """

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: tuple[str, ...] = (),
    ) -> None:
        self._name = _sanitize(name)
        self._documentation = documentation
        self._labelnames = labelnames
        self._values: dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def inc(self, amount: int = 1, **labels: str) -> None:
        """Increment the counter."""
        key = tuple(labels.get(k, "") for k in self._labelnames)
        with self._lock:
            self._values[key] += amount

    def render(self) -> str:
        lines: list[str] = []
        lines.append(f"# HELP {self._name} {self._documentation}")
        lines.append(f"# TYPE {self._name} counter")
        with self._lock:
            items = list(self._values.items())
        for key, value in items:
            labels = dict(zip(self._labelnames, key))
            labels = {k: v for k, v in labels.items() if v}
            lines.append(f"{self._name}{_label_str(labels)} {value}")
        return "\n".join(lines) + "\n"


# ── Gauge ─────────────────────────────────────────────────────────────────────


class Gauge:
    """A gauge metric that can go up and down.

    Thread-safe via a lock.
    """

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: tuple[str, ...] = (),
    ) -> None:
        self._name = _sanitize(name)
        self._documentation = documentation
        self._labelnames = labelnames
        self._values: dict[tuple, int | float] = defaultdict(int)
        self._lock = threading.Lock()

    def inc(self, amount: int | float = 1, **labels: str) -> None:
        key = tuple(labels.get(k, "") for k in self._labelnames)
        with self._lock:
            self._values[key] += amount

    def dec(self, amount: int | float = 1, **labels: str) -> None:
        key = tuple(labels.get(k, "") for k in self._labelnames)
        with self._lock:
            self._values[key] -= amount

    def set(self, value: int | float, **labels: str) -> None:
        key = tuple(labels.get(k, "") for k in self._labelnames)
        with self._lock:
            self._values[key] = value

    def render(self) -> str:
        lines: list[str] = []
        lines.append(f"# HELP {self._name} {self._documentation}")
        lines.append(f"# TYPE {self._name} gauge")
        with self._lock:
            items = list(self._values.items())
        for key, value in items:
            labels = dict(zip(self._labelnames, key))
            labels = {k: v for k, v in labels.items() if v}
            lines.append(f"{self._name}{_label_str(labels)} {value}")
        return "\n".join(lines) + "\n"


# ── Histogram ─────────────────────────────────────────────────────────────────

_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"))


class Histogram:
    """A histogram with cumulative buckets.

    Thread-safe via a lock.
    """

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: tuple[str, ...] = (),
        buckets: tuple[float, ...] = _DEFAULT_BUCKETS,
    ) -> None:
        self._name = _sanitize(name)
        self._documentation = documentation
        self._labelnames = labelnames
        self._buckets = tuple(sorted(buckets))
        self._values: dict[tuple, dict[float, int]] = defaultdict(lambda: {b: 0 for b in buckets})
        self._sums: dict[tuple, float] = defaultdict(float)
        self._counts: dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, **labels: str) -> None:
        """Record an observation."""
        key = tuple(labels.get(k, "") for k in self._labelnames)
        with self._lock:
            self._counts[key] += 1
            self._sums[key] += value
            for b in self._buckets:
                if value <= b:
                    self._values[key][b] += 1

    def render(self) -> str:
        lines: list[str] = []
        lines.append(f"# HELP {self._name} {self._documentation}")
        lines.append(f"# TYPE {self._name} histogram")
        with self._lock:
            keys = list(self._values.keys())
        for key in keys:
            labels = dict(zip(self._labelnames, key))
            clean = {k: v for k, v in labels.items() if v}
            for b in self._buckets:
                all_labels = {**clean, "le": str(b)}
                lines.append(f"{self._name}_bucket{_label_str(all_labels)} {self._values[key][b]}")
            lines.append(f"{self._name}_count{_label_str(clean)} {self._counts[key]}")
            lines.append(f"{self._name}_sum{_label_str(clean)} {self._sums[key]}")
        return "\n".join(lines) + "\n"
