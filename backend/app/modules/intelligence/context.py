"""AnalysisContext — single object passed to every analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from app.modules.intelligence.config import IntelligenceConfig
    from app.modules.intelligence.graph.models import ResearchGraph


@dataclass
class AnalysisContext:
    """Aggregated context delivered to every intelligence analyzer.

    Kept deliberately minimal.  New cross-cutting concerns should be
    added as optional fields with ``None`` defaults so that existing
    analyzers are not affected.
    """

    graph: ResearchGraph
    config: IntelligenceConfig
    investigation_id: str
    execution_id: str | None = None
    logger: object = field(default=None)
