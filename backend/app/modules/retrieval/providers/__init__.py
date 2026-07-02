"""Compatibility shim — re-exports from ``app.core.retrieval``.

This module is a backward-compatibility stub.  All new code should
import directly from ``app.core.retrieval``.
"""

from app.modules.retrieval.providers.arxiv import ArxivProvider  # noqa: F401
from app.modules.retrieval.providers.base import (  # noqa: F401
    BaseProvider,
    BaseRetrievalProvider,
    ProviderMetadata,
    RetrievalResult,
    SearchResult,
)
from app.modules.retrieval.providers.openalex import OpenAlexProvider  # noqa: F401
from app.modules.retrieval.providers.semantic_scholar import (  # noqa: F401
    SemanticScholarProvider,
)
