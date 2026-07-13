"""Tests for ContextBuilder."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.modules.artifact.domain.models import ArtifactType
from app.modules.copilot.context.builder import _ARTIFACT_PRIORITY, ContextBuilder


def _make_artifact(
    artifact_type: ArtifactType,
    payload: dict | None = None,
    status: str = "ready",
) -> MagicMock:
    art = MagicMock(spec=["artifact_type", "status", "payload", "created_at"])
    art.artifact_type = artifact_type
    status_mock = MagicMock()
    status_mock.value = status
    art.status = status_mock
    art.payload = payload
    art.created_at = datetime(2026, 7, 8, tzinfo=UTC)
    return art


AT = ArtifactType


def _make_paper(
    title: str, authors: list[str] | None = None, abstract: str = "", doi: str = ""
) -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.title = title
    p.authors = authors or []
    p.abstract = abstract
    p.doi = doi
    return p


def _make_builder() -> ContextBuilder:
    builder = ContextBuilder(MagicMock())
    builder._artifact_repo = MagicMock()
    builder._paper_repo = MagicMock()
    builder._extraction_repo = MagicMock()
    return builder


def test_build_returns_empty_context_when_no_artifacts() -> None:
    builder = _make_builder()
    builder._artifact_repo.list_by_investigation.return_value = []
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(uuid.uuid4())

    assert context.sections == []
    assert context.char_count == 0
    assert context.truncated is False


def test_build_prioritises_knowledge_package_first() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(
            AT.KNOWLEDGE_PACKAGE, {"key_findings": ["Finding 1"], "summary": "Summary text"}
        ),
        _make_artifact(AT.RESEARCH_LANDSCAPE, {"research_domains": ["ML"]}),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert len(context.sections) == 2
    assert context.sections[0].artifact_type == AT.KNOWLEDGE_PACKAGE
    assert context.sections[1].artifact_type == AT.RESEARCH_LANDSCAPE


def test_build_skips_non_ready_artifacts() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.KNOWLEDGE_PACKAGE, {"summary": "Valid"}, status="ready"),
        _make_artifact(AT.RESEARCH_GAP_REPORT, {"gaps": ["Gap"]}, status="failed"),
        _make_artifact(AT.RESEARCH_LANDSCAPE, {"research_domains": ["NLP"]}, status="pending"),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert len(context.sections) == 1


def test_build_uses_latest_artifact_version() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    old = _make_artifact(AT.KNOWLEDGE_PACKAGE, {"summary": "Old"})
    old.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    new = _make_artifact(AT.KNOWLEDGE_PACKAGE, {"summary": "New"})
    new.created_at = datetime(2026, 7, 8, tzinfo=UTC)

    builder._artifact_repo.list_by_investigation.return_value = [old, new]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert len(context.sections) == 1
    assert "New" in context.sections[0].summary


def test_build_preserves_citation_mappings() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.KNOWLEDGE_PACKAGE, {"key_findings": ["Finding"], "summary": "S"}),
    ]
    paper1 = _make_paper(
        "Attention Is All You Need", authors=["Vaswani"], doi="10.1234/transformer"
    )
    paper2 = _make_paper("BERT", authors=["Devlin"], doi="10.1234/bert")
    builder._paper_repo.list_by_investigation.return_value = [paper1, paper2]

    context = builder.build(inv_id)

    assert context.paper_title_map["Attention Is All You Need"] == str(paper1.id)
    assert context.paper_title_map["BERT"] == str(paper2.id)


def test_build_continues_with_missing_artifacts() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.RESEARCH_LANDSCAPE, {"research_domains": ["ML"]}),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert len(context.sections) == 1
    assert context.sections[0].artifact_type == AT.RESEARCH_LANDSCAPE


def test_build_respects_priority_order() -> None:
    expected = [
        ArtifactType.KNOWLEDGE_PACKAGE,
        ArtifactType.RESEARCH_GAP_REPORT,
        ArtifactType.RESEARCH_LANDSCAPE,
        ArtifactType.PAPER_COLLECTION,
        ArtifactType.VALIDATED_COLLECTION,
    ]
    assert _ARTIFACT_PRIORITY == expected


def test_to_text_includes_all_sections() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.KNOWLEDGE_PACKAGE, {"key_findings": ["Finding"], "summary": "Summary"}),
        _make_artifact(AT.RESEARCH_LANDSCAPE, {"research_domains": ["CV"]}),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)
    text = context.to_text()

    assert "Knowledge Package" in text
    assert "Research Landscape" in text
    assert "Summary" in text
    assert "CV" in text


def test_build_handles_empty_payload() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.KNOWLEDGE_PACKAGE, None),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert context.sections == []


def test_build_knowledge_package_summary() -> None:
    builder = _make_builder()
    payload = {
        "key_findings": ["Finding 1", "Finding 2"],
        "summary": "Overall summary of the investigation.",
        "methodology": "Systematic review",
        "conclusions": "Further research needed.",
    }

    summary = builder._summarise_knowledge_package(payload, 5000)

    assert "Finding 1" in summary
    assert "Finding 2" in summary
    assert "Overall summary" in summary
    assert "Systematic review" in summary


def test_build_gap_report_summary() -> None:
    builder = _make_builder()
    payload = {
        "research_gaps": [
            {"description": "Lack of diverse datasets"},
            {"description": "Limited evaluation metrics"},
        ],
        "opportunities": ["Cross-domain transfer learning"],
    }

    summary = builder._summarise_gap_report(payload, 5000)

    assert "Lack of diverse datasets" in summary
    assert "Limited evaluation metrics" in summary
    assert "Cross-domain transfer learning" in summary


def test_build_landscape_summary() -> None:
    builder = _make_builder()
    payload = {
        "research_domains": ["Computer Vision", "NLP"],
        "methodologies": ["Deep Learning", "Transfer Learning"],
        "technologies": [{"name": "PyTorch"}, {"name": "TensorFlow"}],
        "top_authors": [{"name": "Geoffrey Hinton"}],
    }

    summary = builder._summarise_landscape(payload, [], 5000)

    assert "Computer Vision" in summary
    assert "NLP" in summary
    assert "Deep Learning" in summary
    assert "PyTorch" in summary
    assert "Geoffrey Hinton" in summary


def test_build_handles_malformed_artifact_json() -> None:
    builder = _make_builder()
    inv_id = uuid.uuid4()

    builder._artifact_repo.list_by_investigation.return_value = [
        _make_artifact(AT.KNOWLEDGE_PACKAGE, {"key_findings": None, "summary": None}),
    ]
    builder._paper_repo.list_by_investigation.return_value = []

    context = builder.build(inv_id)

    assert len(context.sections) == 1
    assert context.sections[0].summary == ""
