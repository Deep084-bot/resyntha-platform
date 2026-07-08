"""Abstract embedding provider."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers.

    Subclasses wrap a specific embedding model or API and handle
    vectorisation of text chunks and user questions.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimension."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """Embed a batch of texts into vectors.

        Parameters
        ----------
        texts:
            List of text strings to embed.

        Returns
        -------
        list[np.ndarray]
            One float vector per input text.
        """

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string."""
        return self.embed([query])[0]
