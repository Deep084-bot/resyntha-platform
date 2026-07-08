"""Local embedding provider using sentence-transformers."""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from app.modules.copilot.embeddings.base import EmbeddingProvider
from app.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "all-MiniLM-L6-v2"


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using a local sentence-transformers model.

    The model is loaded lazily on first call to avoid import-time
    downloads.  Default model is ``all-MiniLM-L6-v2`` (384-dim).
    """

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._dim: int | None = None

    @property
    def dimension(self) -> int:
        if self._dim is None:
            model = self._get_model()
            self._dim = model.get_sentence_embedding_dimension()
        return self._dim

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        model = self._get_model()
        if not texts:
            return []
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return [np.array(e, dtype=np.float32) for e in embeddings]

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("loading_embedding_model", model=self._model_name)
            self._model = SentenceTransformer(self._model_name, trust_remote_code=True)
            self._dim = self._model.get_sentence_embedding_dimension()
            logger.info("embedding_model_loaded", model=self._model_name, dim=self._dim)
        return self._model
