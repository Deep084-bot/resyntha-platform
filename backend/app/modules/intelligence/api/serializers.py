"""Mappings from aggregation models to stable API response models."""

from __future__ import annotations

from app.modules.intelligence.aggregation.models import LandscapeResult
from app.modules.intelligence.api.models import LandscapeResponse


def landscape_to_response(landscape: LandscapeResult) -> LandscapeResponse:
    """Convert an internal LandscapeResult into the public LandscapeResponse.

    The ``statistics`` section is intentionally excluded — it is an internal
    aggregation by-product that external consumers should not depend on.
    """
    return LandscapeResponse(
        overview=landscape.overview,
        institutions=landscape.institutions,
        methodologies=landscape.methodologies,
        technologies=landscape.technologies,
        datasets=landscape.datasets,
        temporal=landscape.temporal,
        collaborations=landscape.collaborations,
        observations=landscape.observations,
    )
