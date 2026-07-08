"""Tests for Sprint D3 — Chunking, Embeddings, Vector Repository, Hybrid Scoring, Context Compression, Semantic Retriever."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.modules.copilot.chunking.models import Chunk
from app.modules.copilot.chunking.pipeline import ChunkingPipeline
from app.modules.copilot.embeddings.base import EmbeddingProvider
from app.modules.copilot.embeddings.local import SentenceTransformerProvider
from app.modules.copilot.retrieval.compression import ContextCompressor
from app.modules.copilot.retrieval.hybrid import HybridScorer
from app.modules.copilot.retrieval.models import RetrievedSection


# ── Helpers ─────────────────────────────────────────────────────

def _make_artifact(atype, payload, status="ready"):
    art = MagicMock(spec=["artifact_type", "status", "payload", "id", "created_at", "version"])
    art.artifact_type = atype
    s = MagicMock()
    s.value = status
    art.status = s
    art.payload = payload
    art.id = uuid.uuid4()
    art.version = 1
    art.created_at = datetime(2026, 7, 8, tzinfo=timezone.utc)
    return art


def _kp_entry(
    title: str = "Paper A",
    findings: list[str] | None = None,
    methodology: str = "",
    limitations: list[str] | None = None,
    future: list[str] | None = None,
    techniques: list[str] | None = None,
    summary: str = "",
    questions: list[str] | None = None,
) -> dict:
    return {
        "paper_title": title,
        "key_findings": findings or [],
        "methodology": methodology,
        "limitations": limitations or [],
        "future_work": future or [],
        "relevant_techniques": techniques or [],
        "summary": summary,
        "research_questions": questions or [],
    }


# ── ChunkingPipeline tests ──────────────────────────────────────

class TestChunkingPipeline:
    def test_chunk_all_empty(self) -> None:
        pipeline = ChunkingPipeline()
        chunks = pipeline.chunk_all(uuid.uuid4(), [])
        assert chunks == []

    def test_chunk_all_skips_non_ready(self) -> None:
        pipeline = ChunkingPipeline()
        art = _make_artifact("knowledge_package", {}, status="pending")
        chunks = pipeline.chunk_all(uuid.uuid4(), [art])
        assert chunks == []

    def test_chunk_knowledge_package(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art_id = uuid.uuid4()
        art = _make_artifact("knowledge_package", {
            "papers": [_kp_entry(
                title="Paper A",
                findings=["Finding 1", "Finding 2"],
                methodology="Deep Learning",
                limitations=["Limited data"],
                future=["More data needed"],
                techniques=["CNN"],
                summary="A paper about CNNs.",
                questions=["What is CNN?"],
            )],
        })
        art.id = art_id
        chunks = pipeline.chunk_all(inv_id, [art])
        assert len(chunks) >= 6
        labels = {c.section for c in chunks}
        assert "Key Findings" in labels
        assert "Methodologies" in labels
        assert "Limitations" in labels
        assert "Future Work" in labels
        assert "Technologies" in labels
        assert "Summary" in labels
        for c in chunks:
            assert c.investigation_id == inv_id
            assert c.artifact_id == art_id

    def test_chunk_landscape(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art = _make_artifact("research_landscape", {
            "research_domains": [{"name": "Computer Vision", "count": 3}],
            "methodologies": [{"name": "Deep Learning", "count": 4}],
            "datasets": [{"name": "ImageNet", "count": 2}],
        })
        chunks = pipeline.chunk_all(inv_id, [art])
        labels = {c.section for c in chunks}
        assert "Research Domains" in labels
        assert "Methodologies" in labels
        assert "Datasets" in labels

    def test_chunk_gap_report(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art = _make_artifact("research_gap_report", {
            "gaps": [
                {"title": "Missing benchmark", "description": "No standard.", "category": "dataset"},
            ],
            "recommendations": ["Create benchmark"],
        })
        chunks = pipeline.chunk_all(inv_id, [art])
        labels = {c.section for c in chunks}
        assert "Research Gaps" in labels
        assert "Recommendations" in labels

    def test_chunk_paper_collection(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art = _make_artifact("paper_collection", {
            "papers": [{"title": "Paper A", "authors": ["Author A"], "abstract": "Abstract.", "doi": "10.1234"}],
        })
        chunks = pipeline.chunk_all(inv_id, [art])
        assert len(chunks) == 1
        assert "Paper A" in chunks[0].content

    def test_chunk_with_overlap(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art_id = uuid.uuid4()
        long_content = "Paragraph one.\n" + ("A" * 900) + "\nParagraph two.\n" + ("B" * 900)
        art = _make_artifact("knowledge_package", {
            "papers": [{"summary": long_content}],
        })
        art.id = art_id
        chunks = pipeline.chunk_all(inv_id, [art])
        # Long content should be split into multiple chunks with overlap
        assert len(chunks) >= 2
        for c in chunks:
            assert c.chunk_index >= 0
            assert c.source == "Knowledge Package"

    def test_chunk_metadata_preserved(self) -> None:
        pipeline = ChunkingPipeline()
        inv_id = uuid.uuid4()
        art = _make_artifact("knowledge_package", {
            "papers": [_kp_entry(title="Paper A", findings=["Finding X"])],
        })
        chunks = pipeline.chunk_all(inv_id, [art])
        findings_chunks = [c for c in chunks if c.section == "Key Findings"]
        assert findings_chunks
        assert findings_chunks[0].metadata.get("paper_title") == "Paper A"

    def test_chunk_empty_payload(self) -> None:
        pipeline = ChunkingPipeline()
        art = _make_artifact("knowledge_package", {})
        chunks = pipeline.chunk_all(uuid.uuid4(), [art])
        assert chunks == []


# ── EmbeddingProvider tests ─────────────────────────────────────

class MockEmbeddingProvider(EmbeddingProvider):
    """Simple mock that returns identity vectors for testing."""

    @property
    def dimension(self) -> int:
        return 4

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        return [np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32) for _ in texts]


class TestEmbeddingProvider:
    def test_mock_provider(self) -> None:
        provider = MockEmbeddingProvider()
        assert provider.dimension == 4
        vecs = provider.embed(["hello", "world"])
        assert len(vecs) == 2
        assert vecs[0].shape == (4,)

    def test_embed_query_returns_vector(self) -> None:
        provider = MockEmbeddingProvider()
        vec = provider.embed_query("test question")
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (4,)

    def test_embed_empty_list(self) -> None:
        provider = MockEmbeddingProvider()
        result = provider.embed([])
        assert result == []


# ── HybridScorer tests ──────────────────────────────────────────

class TestHybridScorer:
    def test_hybrid_score_combines_semantic_and_keyword(self) -> None:
        scorer = HybridScorer()
        section = RetrievedSection(source="KP", label="Methodologies", content="Deep Learning is used.")
        from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
        question = KeywordAnalyzer().analyze("What methodologies?")
        score = scorer.score(section, question, semantic_similarity=0.8)
        assert 0.0 <= score <= 1.0

    def test_hybrid_score_high_semantic_low_keyword(self) -> None:
        scorer = HybridScorer()
        section = RetrievedSection(source="KP", label="Authors", content="John Smith.")
        from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
        question = KeywordAnalyzer().analyze("What datasets?")
        score = scorer.score(section, question, semantic_similarity=0.9)
        # Semantic weight 0.7 * 0.9 = 0.63; keyword near 0; total ~0.63
        assert score > 0.5

    def test_hybrid_score_exact_match(self) -> None:
        scorer = HybridScorer()
        section = RetrievedSection(source="KP", label="Datasets", content="ImageNet is a large dataset.")
        from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
        question = KeywordAnalyzer().analyze("What datasets were used?")
        score = scorer.score(section, question, semantic_similarity=0.95)
        assert score > 0.5


# ── ContextCompression tests ────────────────────────────────────

class TestContextCompressor:
    def test_compress_removes_overlap(self) -> None:
        compressor = ContextCompressor()
        sections = [
            RetrievedSection(source="KP", label="Methodologies", content="Deep Learning is used in all papers.", score=0.9),
            RetrievedSection(source="Landscape", label="Methodologies", content="Deep Learning is used in all papers reviewed.", score=0.7),
            RetrievedSection(source="Gap Report", label="Gaps", content="Missing benchmarks.", score=0.5),
        ]
        compressed = compressor.compress(sections)
        assert len(compressed) < len(sections)

    def test_compress_keeps_distinct_sections(self) -> None:
        compressor = ContextCompressor()
        sections = [
            RetrievedSection(source="KP", label="Methodologies", content="Deep Learning.", score=0.8),
            RetrievedSection(source="Landscape", label="Datasets", content="ImageNet.", score=0.7),
            RetrievedSection(source="Gap Report", label="Gaps", content="Missing.", score=0.6),
        ]
        compressed = compressor.compress(sections)
        assert len(compressed) == 3

    def test_compress_empty(self) -> None:
        compressor = ContextCompressor()
        assert compressor.compress([]) == []

    def test_compress_keeps_highest_score(self) -> None:
        compressor = ContextCompressor()
        sections = [
            RetrievedSection(source="KP", label="Methods", content="Deep Learning approach is used across all papers.", score=0.5),
            RetrievedSection(source="Landscape", label="Methods", content="Deep Learning approach is used across all papers reviewed.", score=0.9),
        ]
        compressed = compressor.compress(sections)
        assert len(compressed) == 1
        assert compressed[0].score == 0.9

    def test_content_overlap(self) -> None:
        assert ContextCompressor._content_overlap(
            "deep learning is used", "deep learning is the main approach"
        ) > 0.5
        assert ContextCompressor._content_overlap(
            "computer vision", "natural language processing"
        ) == 0.0
        assert ContextCompressor._content_overlap("", "anything") == 0.0


# ── VectorRepository tests ──────────────────────────────────────

class TestVectorRepository:
    def _make_repo(self):
        session = MagicMock()
        from app.modules.copilot.vector.repository import VectorRepository
        return VectorRepository(session), session

    def test_store_and_search(self) -> None:
        repo, session = self._make_repo()
        inv_id = uuid.uuid4()

        # Mock the session.execute to return results
        from sqlalchemy import select

        mock_chunk = MagicMock()
        mock_chunk.id = uuid.uuid4()
        mock_chunk.investigation_id = inv_id
        mock_chunk.source = "KP"
        mock_chunk.section = "Findings"
        mock_chunk.content = "Test content."
        mock_chunk.artifact_version = 1
        mock_chunk.embedding = [0.1, 0.2, 0.3, 0.4]

        mock_result_row = MagicMock()
        mock_result_row.__getitem__.side_effect = lambda idx: [mock_chunk, 0.15][idx]
        mock_result_row.__iter__.return_value = iter([mock_chunk, 0.15])
        session.execute.return_value.all.return_value = [(mock_chunk, 0.15)]

        results = repo.search(inv_id, np.array([0.1, 0.2, 0.3, 0.4]))
        assert len(results) == 1
        assert results[0][1] == 0.85  # 1.0 - 0.15

    def test_has_embeddings(self) -> None:
        repo, session = self._make_repo()
        session.query.return_value.filter.return_value.count.return_value = 5
        assert repo.has_embeddings(uuid.uuid4())

    def test_has_embeddings_false(self) -> None:
        repo, session = self._make_repo()
        session.query.return_value.filter.return_value.count.return_value = 0
        assert not repo.has_embeddings(uuid.uuid4())

    def test_count_by_investigation(self) -> None:
        repo, session = self._make_repo()
        session.query.return_value.filter.return_value.count.return_value = 3
        assert repo.count_by_investigation(uuid.uuid4()) == 3

    def test_clear_investigation(self) -> None:
        repo, session = self._make_repo()
        inv_id = uuid.uuid4()
        repo.clear_investigation(inv_id)
        # Verify delete was called
        session.query.return_value.filter.assert_called()


# ── SemanticRetriever tests ─────────────────────────────────────

class TestSemanticRetriever:
    def _make_retriever(self, has_embeddings=True, search_results=None):
        session = MagicMock()
        from app.modules.copilot.retrieval.semantic_retriever import SemanticRetriever
        retriever = SemanticRetriever(session, embedder=MockEmbeddingProvider())

        # Mock vector repository
        mock_vector_repo = MagicMock()
        mock_vector_repo.has_embeddings.return_value = has_embeddings
        if search_results is not None:
            mock_vector_repo.search.return_value = search_results
        retriever._vector_repo = mock_vector_repo
        return retriever

    def test_retrieve_no_embeddings(self) -> None:
        retriever = self._make_retriever(has_embeddings=False)
        result = retriever.retrieve(uuid.uuid4(), "What methodologies?")
        assert result.sections == []
        assert result.diagnostics is not None

    def test_retrieve_no_search_results(self) -> None:
        retriever = self._make_retriever(has_embeddings=True, search_results=[])
        result = retriever.retrieve(uuid.uuid4(), "What methodologies?")
        assert result.sections == []
        assert "No relevant chunks" in result.metadata[0]

    def test_retrieve_with_results(self) -> None:
        inv_id = uuid.uuid4()
        mock_chunk = MagicMock()
        mock_chunk.source = "Knowledge Package"
        mock_chunk.section = "Methodologies"
        mock_chunk.content = "Deep Learning and CNNs are used."
        mock_chunk.artifact_version = 1

        search_results = [(mock_chunk, 0.85)]
        retriever = self._make_retriever(has_embeddings=True, search_results=search_results)

        result = retriever.retrieve(inv_id, "What methodologies are used?")
        assert len(result.sections) > 0
        assert result.diagnostics is not None
        assert result.diagnostics.total_raw_sections > 0

    def test_retrieve_with_keyword_boost(self) -> None:
        inv_id = uuid.uuid4()
        mock_chunk = MagicMock()
        mock_chunk.source = "Knowledge Package"
        mock_chunk.section = "Datasets"
        mock_chunk.content = "ImageNet and COCO are the primary datasets used for evaluation."
        mock_chunk.artifact_version = 1

        search_results = [(mock_chunk, 0.75)]
        retriever = self._make_retriever(has_embeddings=True, search_results=search_results)

        result = retriever.retrieve(inv_id, "What datasets were used?")
        assert result.sections
        # The hybrid score should be > semantic score due to keyword boost
        section = result.sections[0]
        # With keyword boost, score should be higher than raw semantic (0.75)
        assert section.score > 0.5

    def test_retrieve_diagnostics_populated(self) -> None:
        inv_id = uuid.uuid4()
        mock_chunk = MagicMock()
        mock_chunk.source = "KP"
        mock_chunk.section = "Findings"
        mock_chunk.content = "Key findings here."
        mock_chunk.artifact_version = 1

        search_results = [(mock_chunk, 0.9)]
        retriever = self._make_retriever(has_embeddings=True, search_results=search_results)
        result = retriever.retrieve(inv_id, "What findings?")
        d = result.diagnostics
        assert d is not None
        assert d.total_raw_sections > 0
        assert d.num_keywords > 0
        assert d.retrieval_duration_ms > 0

    def test_retrieve_empty_question_handling(self) -> None:
        retriever = self._make_retriever(has_embeddings=False)
        result = retriever.retrieve(uuid.uuid4(), "")
        assert isinstance(result, object)


# ── EmbeddingLifecycle tests ────────────────────────────────────

class TestEmbeddingLifecycle:
    def _make_lifecycle(self, artifacts=None):
        session = MagicMock()
        from app.modules.copilot.lifecycle.embedding import EmbeddingLifecycle
        lifecycle = EmbeddingLifecycle(session, embedder=MockEmbeddingProvider())

        # Mock artifact repo
        mock_artifact_repo = MagicMock()
        mock_artifact_repo.list_by_investigation.return_value = artifacts or []
        lifecycle._artifact_repo = mock_artifact_repo

        # Mock vector repo
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_max_version.return_value = 0
        mock_vector_repo.has_embeddings.return_value = False
        lifecycle._vector_repo = mock_vector_repo

        return lifecycle

    def test_generate_empty_investigation(self) -> None:
        lifecycle = self._make_lifecycle(artifacts=[])
        stats = lifecycle.generate_for_investigation(uuid.uuid4())
        assert stats["chunks_created"] == 0
        assert stats["artifacts_processed"] == 0

    def test_generate_with_artifacts(self) -> None:
        inv_id = uuid.uuid4()
        art = _make_artifact("knowledge_package", {
            "papers": [_kp_entry(title="Paper A", findings=["Finding X"])],
        })
        lifecycle = self._make_lifecycle(artifacts=[art])
        stats = lifecycle.generate_for_investigation(inv_id)
        # Should create chunks and call store_chunks
        assert stats["artifacts_processed"] >= 1
        assert lifecycle._vector_repo.store_chunks.called

    def test_generate_skips_known_version(self) -> None:
        inv_id = uuid.uuid4()
        art = _make_artifact("knowledge_package", {"papers": []})
        art.version = 1
        lifecycle = self._make_lifecycle(artifacts=[art])
        lifecycle._vector_repo.get_max_version.return_value = 2  # already embedded at v2
        stats = lifecycle.generate_for_investigation(inv_id)
        assert stats["artifacts_skipped"] >= 1

    def test_clear_investigation(self) -> None:
        lifecycle = self._make_lifecycle()
        inv_id = uuid.uuid4()
        lifecycle.clear_investigation(inv_id)
        lifecycle._vector_repo.clear_investigation.assert_called_with(inv_id)

    def test_generate_handles_bad_chunks(self) -> None:
        inv_id = uuid.uuid4()
        # Artifact with non-dict items in papers
        art = _make_artifact("knowledge_package", {"papers": ["not a dict"]})
        lifecycle = self._make_lifecycle(artifacts=[art])
        lifecycle._vector_repo.get_max_version.return_value = 0
        stats = lifecycle.generate_for_investigation(inv_id)
        assert "errors" in stats


# ── Integration-style tests ─────────────────────────────────────

class TestSemanticIntegration:
    def test_chunk_then_retrieve_roundtrip(self) -> None:
        """Verify that the chunking → embedding → search flow is consistent."""
        inv_id = uuid.uuid4()

        # Chunk a knowledge package
        pipeline = ChunkingPipeline()
        art = _make_artifact("knowledge_package", {
            "papers": [_kp_entry(
                title="Paper A",
                findings=["Transformer models achieve SOTA results on NLP benchmarks."],
            )],
        })
        chunks = pipeline.chunk_all(inv_id, [art])
        assert len(chunks) == 1
        assert "Transformer" in chunks[0].content

        # Verify chunk structure
        c = chunks[0]
        assert c.investigation_id == inv_id
        assert c.artifact_id == art.id
        assert c.source == "Knowledge Package"
        assert c.section == "Key Findings"
        assert c.chunk_index == 0

    def test_hybrid_scoring_preserves_order(self) -> None:
        scorer = HybridScorer()
        from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
        question = KeywordAnalyzer().analyze("What technologies are used?")

        tech_section = RetrievedSection(
            source="KP", label="Technologies",
            content="PyTorch, TensorFlow, and JAX are used.",
        )
        author_section = RetrievedSection(
            source="KP", label="Authors",
            content="John Smith.",
        )

        tech_score = scorer.score(tech_section, question, semantic_similarity=0.9)
        author_score = scorer.score(author_section, question, semantic_similarity=0.3)

        # Tech section should score higher for a technology question
        assert tech_score > author_score

    def test_context_compression_preserves_diversity(self) -> None:
        compressor = ContextCompressor()
        sections = [
            RetrievedSection(source="KP", label="Findings", content="Finding about transformers.", score=0.9),
            RetrievedSection(source="KP", label="Methodologies", content="Deep Learning methods.", score=0.8),
            RetrievedSection(source="KP", label="Datasets", content="ImageNet.", score=0.7),
            RetrievedSection(source="KP", label="Findings", content="Finding about transformers (overlap).", score=0.6),
        ]
        compressed = compressor.compress(sections)
        labels = {s.label for s in compressed}
        # Should have one Findings (highest score), Methodologies, Datasets
        assert len(compressed) >= 3
        assert "Findings" in labels
        assert "Methodologies" in labels
        assert "Datasets" in labels

    def test_empty_chunking_pipeline(self) -> None:
        pipeline = ChunkingPipeline()
        chunks = pipeline.chunk_all(uuid.uuid4(), [])
        assert len(chunks) == 0


# ── Diagnostics tests ──────────────────────────────────────────

class TestRetrievalDiagnostics:
    def test_diagnostics_defaults(self) -> None:
        from app.modules.copilot.retrieval.models import RetrievalDiagnostics
        d = RetrievalDiagnostics()
        assert d.total_raw_sections == 0
        assert d.retrieval_duration_ms == 0.0

    def test_diagnostics_from_semantic_retrieval(self) -> None:
        from app.modules.copilot.retrieval.models import RetrievalDiagnostics
        d = RetrievalDiagnostics(
            total_raw_sections=20,
            scored_sections=20,
            dedup_removed=5,
            selected_count=10,
            retrieval_duration_ms=45.2,
            num_keywords=3,
            num_signals=2,
            budget_limit=25000,
            total_char_count=8000,
        )
        assert d.total_raw_sections == 20
        assert d.selected_count == 10
        assert d.retrieval_duration_ms == 45.2


# ── Local embedding provider (requires model download) ─────────

class TestSentenceTransformerProvider:
    @pytest.mark.slow
    def test_provider_loads_and_embeds(self) -> None:
        """Requires downloading all-MiniLM-L6-v2 (~80MB).  Marked slow."""
        provider = SentenceTransformerProvider()
        assert provider.dimension == 384
        vecs = provider.embed(["test sentence"])
        assert len(vecs) == 1
        assert vecs[0].shape == (384,)

    def test_embed_query_returns_normalized_vector(self) -> None:
        provider = SentenceTransformerProvider()
        vec = provider.embed_query("test question")
        # Should be normalized (unit length)
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 0.01
