"""Stable API response models for the Intelligence layer.

This is the public contract for all external consumers (frontend, Copilot,
REST endpoints, AI agents).  Nothing outside the intelligence package
should need to import from analyzers or aggregation internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.intelligence.aggregation.models import (
    CollaborationSection,
    DatasetSection,
    InstitutionSection,
    MethodologySection,
    Observation,
    OverviewSection,
    TechnologySection,
    TemporalSection,
)


@dataclass
class LandscapeResponse:
    """Top-level research-landscape response.

    Stable subset of LandscapeResult.  Excludes internal-only fields
    such as ``statistics`` and ``institutions_by_type``.
    """

    overview: OverviewSection = field(default_factory=OverviewSection)
    institutions: InstitutionSection = field(default_factory=InstitutionSection)
    methodologies: MethodologySection = field(default_factory=MethodologySection)
    technologies: TechnologySection = field(default_factory=TechnologySection)
    datasets: DatasetSection = field(default_factory=DatasetSection)
    temporal: TemporalSection = field(default_factory=TemporalSection)
    collaborations: CollaborationSection = field(default_factory=CollaborationSection)
    observations: list[Observation] = field(default_factory=list)
