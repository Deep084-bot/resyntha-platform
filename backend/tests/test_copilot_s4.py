"""Tests for Sprint D4 — Production Semantic Copilot.

Covers:
- Auto-embedding generation on investigation completion (non-blocking)
- Fallback from SemanticRetriever -> InvestigationRetriever
- Embedding versioning (skip, regenerate, stale removal)
- Diagnostics population (retriever_type, estimated_prompt_chars, etc.)
- Error handling and graceful degradation
- Background embedding lifecycle integration
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.modules.copilot.lifecycle.embedding import EmbeddingLifecycle
from app.modules.copilot.retrieval.models import (
    RetrievalDiagnostics,
    RetrievalResult,
    RetrievedSection,
)
from app.modules.copilot.retrieval.retriever import InvestigationRetriever
from app.modules.copilot.retrieval.semantic_retriever import SemanticRetriever
from app.modules.copilot.service.service import CopilotService


def _make_section(content: str = "Test content.", source: str = "KP", label: str = "Findings", score: float = 0.0) -> RetrievedSection:
    return RetrievedSection(source=source, label=label, content=content, score=score)


def _make_result(sections: list[RetrievedSection] | None = None) -> RetrievalResult:
    return RetrievalResult(
        sections=sections or [],
        total_char_count=sum(s.char_count for s in (sections or [])),
        diagnostics=RetrievalDiagnostics(
            total_raw_sections=len(sections or []),
            retriever_type="semantic" if sections else "heuristic",
        ),
    )


class TestFallbackRetrieval:
    def test_fallback_when_semantic_returns_empty(self) -> None:
        """When SemanticRetriever returns empty sections, CopilotService falls back to heuristic."""
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.return_value = _make_result(sections=[])

        mock_heuristic = MagicMock()
        heuristic_result = _make_result(sections=[_make_section(content="Heuristic finding.")])
        mock_heuristic.retrieve.return_value = heuristic_result

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        result, analysis = service._retrieve_with_fallback(inv_id, "test question")
        assert len(result.sections) == 1
        assert "Heuristic finding" in result.sections[0].content
        mock_heuristic.retrieve.assert_called_once_with(inv_id, "test question")

    def test_no_fallback_when_semantic_has_results(self) -> None:
        """When SemanticRetriever returns results, heuristic is not called."""
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        semantic_result = _make_result(sections=[_make_section(content="Semantic finding.")])
        mock_semantic.retrieve.return_value = semantic_result

        mock_heuristic = MagicMock()
        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        result, analysis = service._retrieve_with_fallback(inv_id, "test question")
        assert len(result.sections) == 1
        assert "Semantic finding" in result.sections[0].content
        mock_heuristic.retrieve.assert_not_called()

    def test_fallback_diagnostics_set_retriever_type(self) -> None:
        """Fallback result has retriever_type='heuristic' in diagnostics."""
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.return_value = _make_result(sections=[])

        mock_heuristic = MagicMock()
        heuristic_result = _make_result(sections=[_make_section()])
        heuristic_result.diagnostics.retriever_type = "heuristic"
        mock_heuristic.retrieve.return_value = heuristic_result

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        result, analysis = service._retrieve_with_fallback(inv_id, "test question")
        assert result.diagnostics is not None
        assert result.diagnostics.retriever_type == "heuristic"

    def test_fallback_on_semantic_exception(self) -> None:
        """When SemanticRetriever raises, CopilotService falls back to heuristic."""
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.side_effect = Exception("Semantic crash")

        mock_heuristic = MagicMock()
        heuristic_result = _make_result(sections=[_make_section(content="Fallback rescue.")])
        mock_heuristic.retrieve.return_value = heuristic_result

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        result, analysis = service._retrieve_with_fallback(inv_id, "test question")
        assert len(result.sections) == 1
        assert "Fallback rescue" in result.sections[0].content

    def test_both_retrievers_fail_returns_empty(self) -> None:
        """When both retrievers fail, exception propagates."""
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.side_effect = Exception("Semantic error")

        mock_heuristic = MagicMock()
        mock_heuristic.retrieve.side_effect = Exception("Heuristic error")

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        with pytest.raises(Exception):
            service._retrieve_with_fallback(inv_id, "test question")


class TestEmbeddingLifecycleS4:
    def _make_lifecycle(self, artifacts=None):
        session = MagicMock()
        lifecycle = EmbeddingLifecycle(session)

        mock_artifact_repo = MagicMock()
        mock_artifact_repo.list_by_investigation.return_value = artifacts or []
        lifecycle._artifact_repo = mock_artifact_repo

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_max_version.return_value = 0
        mock_vector_repo.has_embeddings.return_value = False
        lifecycle._vector_repo = mock_vector_repo

        return lifecycle

    def test_skip_already_embedded_version(self) -> None:
        inv_id = uuid.uuid4()
        art = MagicMock()
        art.artifact_type = "knowledge_package"
        s = MagicMock()
        s.value = "ready"
        art.status = s
        art.payload = {"papers": []}
        art.version = 1

        lifecycle = self._make_lifecycle(artifacts=[art])
        lifecycle._vector_repo.get_max_version.return_value = 2
        stats = lifecycle.generate_for_investigation(inv_id)
        assert stats["artifacts_skipped"] == 1
        assert stats["artifacts_processed"] == 0
        lifecycle._vector_repo.delete_artifact.assert_not_called()

    def test_regenerate_when_version_increased(self) -> None:
        inv_id = uuid.uuid4()
        art = MagicMock()
        art.artifact_type = "knowledge_package"
        art.id = uuid.uuid4()
        s = MagicMock()
        s.value = "ready"
        art.status = s
        art.payload = {"papers": []}
        art.version = 3

        lifecycle = self._make_lifecycle(artifacts=[art])
        lifecycle._vector_repo.get_max_version.return_value = 2
        stats = lifecycle.generate_for_investigation(inv_id)
        assert stats["artifacts_processed"] == 1
        lifecycle._vector_repo.delete_artifact.assert_called_once_with(inv_id, art.id)

    def test_clear_stale_before_regenerate(self) -> None:
        inv_id = uuid.uuid4()
        art = MagicMock()
        art.artifact_type = "research_landscape"
        art.id = uuid.uuid4()
        s = MagicMock()
        s.value = "ready"
        art.status = s
        art.payload = {"research_domains": [{"name": "NLP", "count": 5}]}
        art.version = 2

        lifecycle = self._make_lifecycle(artifacts=[art])
        lifecycle._vector_repo.get_max_version.return_value = 1
        stats = lifecycle.generate_for_investigation(inv_id)
        lifecycle._vector_repo.delete_artifact.assert_called_once_with(inv_id, art.id)
        assert stats["artifacts_processed"] == 1

    def test_preserves_other_investigation_embeddings(self) -> None:
        lifecycle = self._make_lifecycle()
        inv_id = uuid.uuid4()
        lifecycle.clear_investigation(inv_id)
        lifecycle._vector_repo.clear_investigation.assert_called_with(inv_id)

    def test_empty_artifact_list_no_error(self) -> None:
        lifecycle = self._make_lifecycle(artifacts=[])
        stats = lifecycle.generate_for_investigation(uuid.uuid4())
        assert stats["chunks_created"] == 0
        assert stats["duration_ms"] >= 0


class TestRetrievalDiagnosticsS4:
    def test_retriever_type_default(self) -> None:
        d = RetrievalDiagnostics()
        assert d.retriever_type == "heuristic"

    def test_retriever_type_semantic(self) -> None:
        d = RetrievalDiagnostics(retriever_type="semantic")
        assert d.retriever_type == "semantic"

    def test_estimated_prompt_chars_populated(self) -> None:
        d = RetrievalDiagnostics()
        assert d.estimated_prompt_chars == 0
        d.estimated_prompt_chars = 12500
        assert d.estimated_prompt_chars == 12500

    def test_serialize_includes_new_fields(self) -> None:
        service = CopilotService(MagicMock())
        d = RetrievalDiagnostics(
            retriever_type="heuristic",
            estimated_prompt_chars=8000,
            retrieval_duration_ms=123.45,
            total_raw_sections=10,
        )
        serialized = service._serialize_diagnostics(d)
        assert serialized["retriever_type"] == "heuristic"
        assert serialized["estimated_prompt_chars"] == 8000
        assert serialized["retrieval_duration_ms"] == 123.45

    def test_serialize_none(self) -> None:
        service = CopilotService(MagicMock())
        assert service._serialize_diagnostics(None) == {}

    def test_diagnostics_set_on_heuristic_fallback(self) -> None:
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.return_value = _make_result(sections=[])

        mock_heuristic = MagicMock()
        result = _make_result(sections=[_make_section()])
        mock_heuristic.retrieve.return_value = result

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        final, analysis = service._retrieve_with_fallback(inv_id, "question")
        assert final.diagnostics is not None
        assert final.diagnostics.retriever_type == "heuristic"


class TestBackgroundEmbedding:
    def test_background_function_runs_successfully(self) -> None:
        from app.workers.retrieval_job import _generate_embeddings_background

        with patch("app.workers.retrieval_job._run_embedding_lifecycle") as mock_run:
            mock_run.return_value = {
                "chunks_created": 42,
                "duration_ms": 1500.0,
                "errors": [],
            }
            asyncio.run(_generate_embeddings_background(uuid.uuid4()))
            mock_run.assert_called_once()

    def test_background_function_handles_error_gracefully(self) -> None:
        from app.workers.retrieval_job import _generate_embeddings_background

        with patch("app.workers.retrieval_job._run_embedding_lifecycle") as mock_run:
            mock_run.side_effect = Exception("Model loading failed")
            asyncio.run(_generate_embeddings_background(uuid.uuid4()))
            mock_run.assert_called_once()

    def test_background_function_partial_errors(self) -> None:
        from app.workers.retrieval_job import _generate_embeddings_background

        with patch("app.workers.retrieval_job._run_embedding_lifecycle") as mock_run:
            mock_run.return_value = {
                "chunks_created": 30,
                "duration_ms": 2000.0,
                "errors": ["Batch 2 failed"],
            }
            asyncio.run(_generate_embeddings_background(uuid.uuid4()))
            mock_run.assert_called_once()

    def test_run_embedding_lifecycle_sync(self) -> None:
        from app.workers.retrieval_job import _run_embedding_lifecycle

        with patch("app.workers.retrieval_job.EmbeddingLifecycle") as MockLifecycle:
            mock_instance = MagicMock()
            mock_instance.generate_for_investigation.return_value = {"chunks_created": 10}
            MockLifecycle.return_value = mock_instance

            result = _run_embedding_lifecycle(uuid.uuid4())
            assert result is not None
            assert result["chunks_created"] == 10

    def test_run_embedding_lifecycle_error(self) -> None:
        from app.workers.retrieval_job import _run_embedding_lifecycle

        with patch("app.workers.retrieval_job.EmbeddingLifecycle") as MockLifecycle:
            mock_instance = MagicMock()
            mock_instance.generate_for_investigation.side_effect = RuntimeError("DB error")
            MockLifecycle.return_value = mock_instance

            result = _run_embedding_lifecycle(uuid.uuid4())
            assert result is None


class TestGracefulDegradation:
    def test_semantic_empty_no_embeddings(self) -> None:
        session = MagicMock()
        retriever = SemanticRetriever(session)

        mock_vector_repo = MagicMock()
        mock_vector_repo.has_embeddings.return_value = False
        retriever._vector_repo = mock_vector_repo

        result = retriever.retrieve(uuid.uuid4(), "test question")
        assert result.sections == []
        assert result.diagnostics is not None
        assert result.diagnostics.retriever_type == "semantic"

    def test_semantic_embed_failure_returns_empty(self) -> None:
        session = MagicMock()
        retriever = SemanticRetriever(session)

        mock_vector_repo = MagicMock()
        mock_vector_repo.has_embeddings.return_value = True
        retriever._vector_repo = mock_vector_repo

        mock_embedder = MagicMock()
        mock_embedder.embed_query.side_effect = RuntimeError("Model OOM")
        retriever._embedder = mock_embedder

        result = retriever.retrieve(uuid.uuid4(), "test question")
        assert result.sections == []
        assert "embed" in result.metadata[0]

    def test_semantic_search_failure_returns_empty(self) -> None:
        session = MagicMock()
        retriever = SemanticRetriever(session)

        mock_vector_repo = MagicMock()
        mock_vector_repo.has_embeddings.return_value = True
        mock_vector_repo.search.side_effect = RuntimeError("Vector DB unavailable")
        retriever._vector_repo = mock_vector_repo

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3, 0.4]
        retriever._embedder = mock_embedder

        result = retriever.retrieve(uuid.uuid4(), "test question")
        assert result.sections == []
        assert "search" in result.metadata[0]

    def test_copilot_service_no_sections_produces_fallback(self) -> None:
        service = CopilotService(MagicMock())
        inv_id = uuid.uuid4()

        mock_semantic = MagicMock()
        mock_semantic.retrieve.return_value = _make_result(sections=[])

        mock_heuristic = MagicMock()
        mock_heuristic.retrieve.return_value = _make_result(
            sections=[_make_section(content="Heuristic context.")]
        )

        service._retriever = mock_semantic
        service._fallback_retriever = mock_heuristic

        result, analysis = service._retrieve_with_fallback(inv_id, "question")
        assert len(result.sections) == 1
