"""IntelligenceService — the stable public entry point for all consumers.

Orchestrates aggregation + presentation without performing either itself.
"""

from __future__ import annotations

from typing import Any

from app.modules.intelligence.aggregation import LandscapeAggregator
from app.modules.intelligence.analyzers.models import AnalysisResults
from app.modules.intelligence.api.models import LandscapeResponse
from app.modules.intelligence.api.serializers import landscape_to_response
from app.modules.intelligence.presentation import JsonRenderer, MarkdownRenderer


class IntelligenceService:
    """Public interface to the Intelligence Engine.

    Thin orchestrator — no aggregation, no rendering, no graph traversal.
    """

    def __init__(
        self,
        aggregator: LandscapeAggregator | None = None,
        markdown_renderer: MarkdownRenderer | None = None,
        json_renderer: JsonRenderer | None = None,
    ) -> None:
        self._aggregator = aggregator or LandscapeAggregator()
        self._markdown_renderer = markdown_renderer or MarkdownRenderer()
        self._json_renderer = json_renderer or JsonRenderer()

    def get_landscape(self, results: AnalysisResults) -> LandscapeResponse:
        """Aggregate and return the stable landscape response model."""
        landscape = self._aggregator.aggregate(results)
        return landscape_to_response(landscape)

    def get_markdown(self, results: AnalysisResults) -> str:
        """Aggregate and render as Markdown string."""
        landscape = self._aggregator.aggregate(results)
        return self._markdown_renderer.render(landscape)

    def get_json(self, results: AnalysisResults) -> dict[str, Any]:
        """Aggregate and render as a JSON-serialisable dictionary."""
        landscape = self._aggregator.aggregate(results)
        return self._json_renderer.render(landscape)
