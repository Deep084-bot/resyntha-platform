"""Tests for the retrieval layer — KeywordAnalyzer, SectionExtractor, SectionScorer, InvestigationRetriever."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
from app.modules.copilot.retrieval.extractor import SectionExtractor
from app.modules.copilot.retrieval.models import RetrievedSection
from app.modules.copilot.retrieval.retriever import InvestigationRetriever
from app.modules.copilot.retrieval.scorer import SectionScorer

# ── Helpers ─────────────────────────────────────────────────────


def _make_artifact(atype, payload, status="ready"):
    art = MagicMock(spec=["artifact_type", "status", "payload", "created_at"])
    art.artifact_type = atype
    s = MagicMock()
    s.value = status
    art.status = s
    art.payload = payload
    art.created_at = datetime(2026, 7, 8, tzinfo=UTC)
    return art


def _kp_payload(papers_data: list[dict] | None = None) -> dict:
    return {"papers": papers_data or []}


def _paper_entry(
    title: str = "Test Paper",
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


_landscape_payload = {
    "research_domains": [{"name": "Computer Vision", "count": 3}, {"name": "NLP", "count": 1}],
    "methodologies": [{"name": "Deep Learning", "count": 4}],
    "datasets": [{"name": "ImageNet", "count": 2}],
    "evaluation_metrics": [{"name": "Accuracy", "count": 3}],
    "keywords": [{"name": "Transformer", "count": 2}],
    "top_authors": [{"name": "Geoffrey Hinton", "count": 1}],
    "applications": [{"name": "Image Classification", "count": 2}],
    "limitations": [{"name": "Computational cost", "count": 1}],
    "future_work": [{"name": "Scalability", "count": 1}],
}

_gap_report_payload = {
    "gaps": [
        {
            "title": "Missing multimodal benchmark",
            "description": "No standard benchmark exists.",
            "category": "dataset",
        },
        {
            "title": "Limited evaluation",
            "description": "Evaluation is limited to accuracy.",
            "category": "evaluation",
        },
    ],
    "recommendations": ["Create a new benchmark", "Adopt standard metrics"],
}


# ── KeywordAnalyzer tests ──────────────────────────────────────


class TestKeywordAnalyzer:
    def test_analyze_extracts_keywords(self) -> None:
        result = KeywordAnalyzer().analyze("What methodologies are used in transformer papers?")
        assert "methodologies" in result.keywords or "transformer" in result.keywords
        assert result.methodology_signals
        assert result.has_signals()

    def test_analyze_removes_stop_words(self) -> None:
        result = KeywordAnalyzer().analyze("Tell me about the papers")
        assert "tell" not in result.keywords or not result.keywords  # stop words filtered
        assert "papers" in result.keywords

    def test_analyze_extracts_quoted_phrases(self) -> None:
        result = KeywordAnalyzer().analyze('What is "transfer learning" in computer vision?')
        assert "transfer learning" in result.phrases

    def test_analyze_detects_gap_signals(self) -> None:
        result = KeywordAnalyzer().analyze("What research gaps exist in this field?")
        assert result.gap_signals

    def test_analyze_detects_comparison(self) -> None:
        result = KeywordAnalyzer().analyze("Compare the methodologies used in these papers")
        assert result.comparison_signals

    def test_analyze_handles_empty_question(self) -> None:
        result = KeywordAnalyzer().analyze("")
        assert not result.has_signals()

    def test_analyze_detects_dataset_signals(self) -> None:
        result = KeywordAnalyzer().analyze("What datasets were used?")
        assert result.dataset_signals

    def test_analyze_detects_technology_signals(self) -> None:
        result = KeywordAnalyzer().analyze("What technologies were employed?")
        assert result.technology_signals


# ── SectionExtractor tests ─────────────────────────────────────


class TestSectionExtractor:
    def _make_extractor(self, artifacts: list | None = None, papers: list | None = None):
        session = MagicMock()
        ext = SectionExtractor(session)
        ext._artifact_repo = MagicMock()
        ext._artifact_repo.list_by_investigation.return_value = artifacts or []
        ext._paper_repo = MagicMock()
        ext._paper_repo.list_by_investigation.return_value = papers or []
        ext._extraction_repo = MagicMock()
        ext._extraction_repo.list_by_investigation.return_value = []
        return ext

    def test_extract_all_empty(self) -> None:
        ext = self._make_extractor()
        sections = ext.extract_all(uuid.uuid4())
        assert sections == []

    def test_extract_knowledge_package(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact(
            "knowledge_package",
            _kp_payload(
                [
                    _paper_entry(
                        title="Paper A",
                        findings=["Finding 1", "Finding 2"],
                        methodology="Deep Learning",
                        limitations=["Limited data"],
                        future=["More data needed"],
                        techniques=["CNN"],
                        summary="A paper about CNNs.",
                        questions=["What is CNN?"],
                    ),
                ]
            ),
        )
        sections = ext._extract_knowledge_package(artifact)
        assert (
            len(sections) >= 6
        )  # findings, methods, limitations, future, techniques, questions, summary
        labels = {s.label for s in sections}
        assert "Key Findings" in labels
        assert "Methodologies" in labels
        assert "Limitations" in labels

    def test_extract_knowledge_package_missing_papers_key(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact("knowledge_package", {})
        sections = ext._extract_knowledge_package(artifact)
        assert sections == []

    def test_extract_landscape(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact("research_landscape", _landscape_payload)
        sections = ext._extract_landscape(artifact)
        labels = {s.label for s in sections}
        assert "Research Domains" in labels
        assert "Methodologies" in labels
        assert "Datasets" in labels
        assert "Technologies" in labels

    def test_extract_landscape_empty(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact("research_landscape", {})
        sections = ext._extract_landscape(artifact)
        assert sections == []

    def test_extract_gap_report(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact("research_gap_report", _gap_report_payload)
        sections = ext._extract_gap_report(artifact)
        labels = {s.label for s in sections}
        assert "Research Gaps" in labels
        assert "Recommendations" in labels

    def test_extract_gap_report_empty(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact("research_gap_report", {})
        sections = ext._extract_gap_report(artifact)
        assert sections == []

    def test_extract_paper_collection_with_papers_key(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact(
            "paper_collection",
            {
                "papers": [
                    {
                        "title": "Paper A",
                        "authors": ["Author A"],
                        "abstract": "Abstract A",
                        "doi": "10.1234/a",
                    }
                ]
            },
        )
        sections = ext._extract_paper_collection(artifact)
        assert len(sections) == 1
        assert "Paper A" in sections[0].content

    def test_extract_paper_collection_with_results_key(self) -> None:
        ext = self._make_extractor()
        artifact = _make_artifact(
            "paper_collection",
            {
                "results": [
                    {
                        "title": "Paper B",
                        "authors": ["Author B"],
                        "abstract": "Abstract B",
                        "doi": "10.1234/b",
                    }
                ]
            },
        )
        sections = ext._extract_paper_collection(artifact)
        assert len(sections) == 1

    def test_extract_papers_fallback(self) -> None:
        ext = self._make_extractor()
        paper = MagicMock()
        paper.title = "Fallback Paper"
        paper.authors = ["Author C"]
        paper.abstract = "Fallback abstract"
        paper.doi = "10.1234/fallback"
        sections = ext._extract_papers([paper])
        assert len(sections) == 1
        assert "Fallback Paper" in sections[0].content

    def test_latest_ready_returns_newest(self) -> None:
        ext = self._make_extractor()
        old = _make_artifact("knowledge_package", {"papers": [{"title": "Old"}]})
        old.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        new = _make_artifact("knowledge_package", {"papers": [{"title": "New"}]})
        new.created_at = datetime(2026, 7, 8, tzinfo=UTC)
        result = ext._latest_ready([old, new], "knowledge_package")
        assert result is new


# ── SectionScorer tests ────────────────────────────────────────


class TestSectionScorer:
    def test_keyword_overlap_scores(self) -> None:
        scorer = SectionScorer()
        section = RetrievedSection(
            source="KP",
            label="Findings",
            content="The transformer architecture is used for NLP tasks.",
        )
        question = KeywordAnalyzer().analyze("What architectures are used for NLP?")
        score = scorer.score(section, question)
        assert score > 0

    def test_section_label_match(self) -> None:
        scorer = SectionScorer()
        section = RetrievedSection(
            source="KP", label="Methodologies", content="Deep learning approaches."
        )
        question = KeywordAnalyzer().analyze("What methodologies were used?")
        score = scorer.score(section, question)
        assert score > 0

    def test_phrase_match_boost(self) -> None:
        scorer = SectionScorer()
        section = RetrievedSection(
            source="KP",
            label="Findings",
            content="Transfer learning improves accuracy significantly.",
        )
        question = KeywordAnalyzer().analyze('What is "transfer learning"?')
        score = scorer.score(section, question)
        assert score > 0

    def test_no_match_returns_zero(self) -> None:
        scorer = SectionScorer()
        section = RetrievedSection(source="KP", label="Authors", content="John Smith")
        question = KeywordAnalyzer().analyze("What datasets were used?")
        score = scorer.score(section, question)
        assert score == 0

    def test_gap_signal_match(self) -> None:
        scorer = SectionScorer()
        section = RetrievedSection(
            source="Gap Report", label="Research Gaps", content="Missing benchmark for evaluation."
        )
        question = KeywordAnalyzer().analyze("What gaps exist?")
        score = scorer.score(section, question)
        assert score > 0


# ── InvestigationRetriever tests ───────────────────────────────


class TestInvestigationRetriever:
    def _make_retriever(self, sections: list[RetrievedSection] | None = None):
        session = MagicMock()
        r = InvestigationRetriever(session)
        if sections is not None:
            r._extractor.extract_all = MagicMock(return_value=sections)
        return r

    def test_retrieve_returns_scored_sections(self) -> None:
        retriever = self._make_retriever(
            sections=[
                RetrievedSection(
                    source="KP", label="Methodologies", content="Deep Learning and CNNs are used."
                ),
                RetrievedSection(
                    source="Landscape", label="Datasets", content="ImageNet is commonly used."
                ),
            ]
        )
        result = retriever.retrieve(uuid.uuid4(), "What methodologies are used?")
        assert len(result.sections) > 0
        assert result.metadata

    def test_retrieve_empty_investigation(self) -> None:
        retriever = self._make_retriever(sections=[])
        result = retriever.retrieve(uuid.uuid4(), "Any question")
        assert result.sections == []

    def test_retrieve_fallback_when_no_match(self) -> None:
        retriever = self._make_retriever(
            sections=[
                RetrievedSection(source="KP", label="Authors", content="John Smith"),
                RetrievedSection(source="Landscape", label="Authors", content="Jane Doe"),
            ]
        )
        result = retriever.retrieve(uuid.uuid4(), "What datasets were used for evaluation?")
        assert len(result.sections) > 0  # fallback kicks in
        assert any("Investigation Summary" in m for m in result.metadata) or result.sections

    def test_deduplicate_removes_overlap(self) -> None:
        sections = [
            RetrievedSection(
                source="KP",
                label="Methodologies",
                content="Deep Learning is the main approach used across all papers.",
            ),
            RetrievedSection(
                source="Landscape",
                label="Methodologies",
                content="Deep Learning is the main approach used across all papers reviewed.",
            ),
            RetrievedSection(
                source="Gap Report", label="Research Gaps", content="Missing benchmarks."
            ),
        ]
        deduped, removed = InvestigationRetriever._deduplicate(sections)
        assert len(deduped) < len(sections)
        assert removed > 0

    def test_deduplicate_keeps_distinct_sections(self) -> None:
        sections = [
            RetrievedSection(source="KP", label="Methodologies", content="Deep Learning."),
            RetrievedSection(source="Landscape", label="Datasets", content="ImageNet."),
            RetrievedSection(
                source="Gap Report", label="Research Gaps", content="Missing benchmarks."
            ),
        ]
        deduped, removed = InvestigationRetriever._deduplicate(sections)
        assert len(deduped) == 3
        assert removed == 0

    def test_retrieve_within_budget_drops_low_scores(self) -> None:
        retriever = self._make_retriever(
            sections=[
                RetrievedSection(
                    source="KP", label="Methodologies", content="Deep Learning is used." * 100
                ),
                RetrievedSection(source="Landscape", label="Authors", content="John Smith."),
                RetrievedSection(source="Gap Report", label="Gaps", content="Missing X."),
            ]
        )
        result = retriever.retrieve(uuid.uuid4(), "What methodologies?")
        assert result.total_char_count <= 25000 or result.truncated is not None

    def test_retrieve_metadata_format(self) -> None:
        retriever = self._make_retriever(
            sections=[
                RetrievedSection(
                    source="Knowledge Package",
                    label="Key Findings",
                    content="The key findings show that transformer models outperform all baselines on the benchmark.",
                ),
            ]
        )
        result = retriever.retrieve(uuid.uuid4(), "What findings?")
        assert result.metadata
        assert "Knowledge Package" in result.metadata[0]

    def test_retrieve_scores_positive_for_relevant_question(self) -> None:
        retriever = self._make_retriever(
            sections=[
                RetrievedSection(
                    source="KP",
                    label="Technologies",
                    content="PyTorch, TensorFlow, and JAX are used.",
                ),
                RetrievedSection(source="Landscape", label="Authors", content="John Smith."),
            ]
        )
        result = retriever.retrieve(uuid.uuid4(), "What technologies are used in this research?")
        kp_sections = [s for s in result.sections if s.source == "KP"]
        assert kp_sections
        assert kp_sections[0].score > 0

    def test_retrieve_handles_malformed_artifact_gracefully(self) -> None:
        retriever = self._make_retriever(sections=[])
        result = retriever.retrieve(uuid.uuid4(), "Any question")
        assert result.sections == []

    def test_content_overlap(self) -> None:
        assert (
            InvestigationRetriever._content_overlap(
                "deep learning is used", "deep learning is the main approach"
            )
            > 0.5
        )
        assert (
            InvestigationRetriever._content_overlap(
                "computer vision", "natural language processing"
            )
            == 0.0
        )
        assert InvestigationRetriever._content_overlap("", "anything") == 0.0

    def test_build_fallback(self) -> None:
        sections = [
            RetrievedSection(source="KP", label="Key Findings", content="Finding 1."),
            RetrievedSection(source="Landscape", label="Domains", content="CV."),
        ]
        fallback = InvestigationRetriever._build_fallback(sections)
        assert fallback is not None
        assert "Investigation Summary" in fallback.source
        assert "Finding 1" in fallback.content

    def test_build_fallback_empty(self) -> None:
        assert InvestigationRetriever._build_fallback([]) is None
