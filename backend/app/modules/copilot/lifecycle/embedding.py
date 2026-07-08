"""Embedding lifecycle — generates and manages embeddings for an investigation."""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.copilot.chunking.pipeline import ChunkingPipeline
from app.modules.copilot.embeddings.base import EmbeddingProvider
from app.modules.copilot.embeddings.factory import create_embedding_provider
from app.modules.copilot.vector.repository import VectorRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)


class EmbeddingLifecycle:
    """Manages the creation and regeneration of embeddings for an investigation.

    Usage (to be called after investigation artifacts are ready)::

        lifecycle = EmbeddingLifecycle(session)
        lifecycle.generate_for_investigation(investigation_id)
    """

    _INTERESTING_TYPES = {
        ArtifactType.KNOWLEDGE_PACKAGE,
        ArtifactType.RESEARCH_LANDSCAPE,
        ArtifactType.RESEARCH_GAP_REPORT,
        ArtifactType.PAPER_COLLECTION,
        ArtifactType.VALIDATED_COLLECTION,
    }

    def __init__(
        self,
        session: Session,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._artifact_repo = ArtifactRepository(session)
        self._vector_repo = VectorRepository(session)
        self._chunker = ChunkingPipeline()
        if embedder is not None:
            self._embedder = embedder
        else:
            self._embedder = create_embedding_provider("local")

    def generate_for_investigation(
        self, investigation_id: uuid.UUID,
    ) -> dict:
        """Generate embeddings for all ready artifacts in an investigation.

        Skips artifacts whose version is already embedded (version-aware).
        Clears stale embeddings for artifacts that have been re-generated.

        Returns a dict with timing/metadata about the operation.
        """
        start = time.perf_counter()
        stats: dict = {
            "investigation_id": str(investigation_id),
            "chunks_created": 0,
            "chunks_skipped": 0,
            "artifacts_processed": 0,
            "artifacts_skipped": 0,
            "duration_ms": 0.0,
            "errors": [],
        }

        artifacts = self._artifact_repo.list_by_investigation(investigation_id)
        ready_artifacts = [
            a for a in artifacts
            if a.artifact_type in self._INTERESTING_TYPES
            and a.status.value == "ready"
        ]

        if not ready_artifacts:
            stats["duration_ms"] = (time.perf_counter() - start) * 1000
            return stats

        # Check current max version
        current_max = self._vector_repo.get_max_version(investigation_id)

        # Chunk each artifact
        all_chunks: list = []
        for artifact in ready_artifacts:
            if artifact.version and artifact.version <= current_max:
                stats["artifacts_skipped"] += 1
                continue

            # Clear stale data for this artifact
            self._vector_repo.delete_artifact(investigation_id, artifact.id)

            chunks = self._chunker.chunk_all(investigation_id, [artifact])
            all_chunks.extend(chunks)
            stats["artifacts_processed"] += 1

        if not all_chunks:
            stats["duration_ms"] = (time.perf_counter() - start) * 1000
            return stats

        # Generate embeddings in batches
        batch_size = 32
        version = current_max + 1

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]
            try:
                embeddings = self._embedder.embed(texts)
                self._vector_repo.store_chunks(batch, embeddings, artifact_version=version)
                stats["chunks_created"] += len(batch)
            except Exception as exc:
                logger.error("embedding_generation_error", error=str(exc)[:500], batch_start=i)
                stats["errors"].append(str(exc)[:200])

        stats["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "embedding_lifecycle_complete",
            investigation_id=str(investigation_id),
            chunks_created=stats["chunks_created"],
            chunks_skipped=stats["chunks_skipped"],
            duration_ms=stats["duration_ms"],
        )
        return stats

    def clear_investigation(self, investigation_id: uuid.UUID) -> None:
        self._vector_repo.clear_investigation(investigation_id)
        logger.info("embedding_cleared", investigation_id=str(investigation_id))
