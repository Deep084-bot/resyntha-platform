"""Embedding provider factory."""

from __future__ import annotations

from app.modules.copilot.embeddings.base import EmbeddingProvider
from app.modules.copilot.embeddings.local import SentenceTransformerProvider


def create_embedding_provider(provider: str | None = None) -> EmbeddingProvider:
    """Create an embedding provider based on configuration.

    Parameters
    ----------
    provider:
        Provider type string.  ``None`` or ``"local"`` returns the
        default sentence-transformers provider.

    Returns
    -------
    EmbeddingProvider
    """
    if provider is None or provider == "local":
        return SentenceTransformerProvider()
    msg = f"Unknown embedding provider: {provider}"
    raise ValueError(msg)
