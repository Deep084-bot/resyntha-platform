"""Compatibility shim — re-exports from ``app.core.retrieval.base``.

This module is a backward-compatibility stub.  All new code should
import directly from ``app.core.retrieval``.
"""

from app.core.retrieval.base import (
    BaseRetrievalProvider,
    ProviderMetadata,
    RetrievalResult,
)

# Backward-compatibility aliases (old names used before Sprint 1).
BaseProvider = BaseRetrievalProvider
SearchResult = RetrievalResult

__all__ = [
    "BaseProvider",
    "BaseRetrievalProvider",
    "ProviderMetadata",
    "RetrievalResult",
    "SearchResult",
]
