"""Repository for chunk embedding CRUD and vector search."""

from __future__ import annotations

import uuid

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.copilot.chunking.models import Chunk
from app.modules.copilot.vector.models import ChunkEmbedding


class VectorRepository:
    """Manages chunk embeddings in the pgvector-backed ``chunk_embeddings`` table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Write ───────────────────────────────────────────────────

    def store_chunk(
        self, chunk: Chunk, embedding: np.ndarray, artifact_version: int = 0
    ) -> ChunkEmbedding:
        row = ChunkEmbedding(
            investigation_id=chunk.investigation_id,
            artifact_id=chunk.artifact_id,
            paper_id=chunk.paper_id,
            section=chunk.section,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            chunk_metadata=chunk.metadata,
            embedding=embedding.tolist(),
            artifact_version=artifact_version,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def store_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[np.ndarray],
        artifact_version: int = 0,
    ) -> list[ChunkEmbedding]:
        if not chunks or not embeddings or len(chunks) != len(embeddings):
            return []
        rows: list[ChunkEmbedding] = []
        for chunk, emb in zip(chunks, embeddings, strict=False):
            rows.append(self.store_chunk(chunk, emb, artifact_version))
        return rows

    def clear_investigation(self, investigation_id: uuid.UUID) -> None:
        self._session.query(ChunkEmbedding).filter(
            ChunkEmbedding.investigation_id == investigation_id,
        ).delete()
        self._session.flush()

    def delete_artifact(self, investigation_id: uuid.UUID, artifact_id: uuid.UUID) -> None:
        self._session.query(ChunkEmbedding).filter(
            ChunkEmbedding.investigation_id == investigation_id,
            ChunkEmbedding.artifact_id == artifact_id,
        ).delete()
        self._session.flush()

    # ── Read ────────────────────────────────────────────────────

    def count_by_investigation(self, investigation_id: uuid.UUID) -> int:
        return (
            self._session.query(ChunkEmbedding)
            .filter(
                ChunkEmbedding.investigation_id == investigation_id,
            )
            .count()
        )

    def get_max_version(self, investigation_id: uuid.UUID) -> int:
        result = self._session.execute(
            select(text("coalesce(max(artifact_version), 0)"))
            .select_from(ChunkEmbedding)
            .where(
                ChunkEmbedding.investigation_id == investigation_id,
            )
        )
        row = result.one()
        return int(row[0]) if row else 0

    def has_embeddings(self, investigation_id: uuid.UUID) -> bool:
        return self.count_by_investigation(investigation_id) > 0

    # ── Vector Search ───────────────────────────────────────────

    def search(
        self,
        investigation_id: uuid.UUID,
        query_embedding: np.ndarray,
        top_k: int = 20,
        min_score: float = 0.0,
    ) -> list[tuple[ChunkEmbedding, float]]:
        """Perform cosine similarity search using pgvector.

        Returns list of (ChunkEmbedding, similarity_score) sorted by
        descending similarity.
        """
        embedding_list = query_embedding.tolist()
        distance_expr = ChunkEmbedding.embedding.cosine_distance(embedding_list)

        stmt = (
            select(ChunkEmbedding, distance_expr.label("distance"))
            .filter(ChunkEmbedding.investigation_id == investigation_id)
            .filter(ChunkEmbedding.embedding.isnot(None))
            .order_by(distance_expr)
            .limit(top_k)
        )
        rows = self._session.execute(stmt).all()

        results: list[tuple[ChunkEmbedding, float]] = []
        for row in rows:
            chunk_emb = row[0]
            distance = float(row[1])
            similarity = 1.0 - distance
            if similarity >= min_score:
                results.append((chunk_emb, similarity))
        return results

    # ── Bulk fetch (for query-time use) ─────────────────────────

    def get_chunks_by_ids(self, chunk_ids: list[uuid.UUID]) -> list[ChunkEmbedding]:
        if not chunk_ids:
            return []
        return self._session.query(ChunkEmbedding).filter(ChunkEmbedding.id.in_(chunk_ids)).all()
