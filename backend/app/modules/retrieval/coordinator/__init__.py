"""Coordinator pattern — orchestrates providers, merges, deduplicates, and ranks."""

from app.modules.retrieval.coordinator.coordinator import RetrievalCoordinator
from app.modules.retrieval.coordinator.merger import MetadataMerger
from app.modules.retrieval.coordinator.ranking import RankingEngine
from app.modules.retrieval.coordinator.resolver import DuplicateResolver

__all__ = [
    "RetrievalCoordinator",
    "MetadataMerger",
    "DuplicateResolver",
    "RankingEngine",
]
