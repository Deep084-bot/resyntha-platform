"""Tests for Copilot Quality components — CitationValidator, ConfidenceCalibrator, FollowUpGenerator."""

from __future__ import annotations

from app.modules.copilot.quality.confidence import ConfidenceCalibrator
from app.modules.copilot.quality.followup import FollowUpGenerator
from app.modules.copilot.quality.validator import CitationValidator
from app.modules.copilot.retrieval.models import (
    RetrievalResult,
    RetrievedSection,
)
from app.modules.copilot.schemas.response import Citation

# ── CitationValidator tests ────────────────────────────────────


class TestCitationValidator:
    def _make_retrieved(self, sections: list[RetrievedSection] | None = None) -> RetrievalResult:
        return RetrievalResult(sections=sections or [])

    def test_validate_empty_citations(self) -> None:
        validator = CitationValidator()
        result = validator.validate([], self._make_retrieved())
        assert result.total_examined == 0
        assert result.validated == []
        assert result.discarded == []

    def test_validate_keeps_matching_citation(self) -> None:
        validator = CitationValidator()
        retrieved = self._make_retrieved(
            [
                RetrievedSection(
                    source="KP", label="Papers", content="Attention Is All You Need is a key paper."
                ),
            ]
        )
        result = validator.validate(
            [{"paper_title": "Attention Is All You Need", "relevance": "Core reference"}],
            retrieved,
        )
        assert result.kept_count == 1
        assert result.discarded_count == 0
        assert result.total_examined == 1

    def test_validate_discards_hallucinated_citation(self) -> None:
        validator = CitationValidator()
        retrieved = self._make_retrieved(
            [
                RetrievedSection(
                    source="KP", label="Papers", content="Deep Learning is discussed."
                ),
            ]
        )
        result = validator.validate(
            [{"paper_title": "Nonexistent Paper 2024", "relevance": "Key"}],
            retrieved,
        )
        assert result.kept_count == 0
        assert result.discarded_count == 1

    def test_validate_mixed_citations(self) -> None:
        validator = CitationValidator()
        retrieved = self._make_retrieved(
            [
                RetrievedSection(
                    source="KP", label="Papers", content="Paper A and Paper B are discussed."
                ),
            ]
        )
        result = validator.validate(
            [
                {"paper_title": "Paper A", "relevance": "Relevant"},
                {"paper_title": "Paper B", "relevance": "Relevant"},
                {"paper_title": "Paper C", "relevance": "Hallucinated"},
            ],
            retrieved,
        )
        assert result.kept_count == 2
        assert result.discarded_count == 1

    def test_validate_empty_title_returns_false(self) -> None:
        validator = CitationValidator()
        assert validator._citation_exists("", "Some context") is False

    def test_validate_fuzzy_title_match(self) -> None:
        validator = CitationValidator()
        assert validator._citation_exists(
            "Attention Is All You Need (Vaswani et al., 2017)",
            "The paper Attention Is All You Need was published in 2017.",
        )

    def test_success_ratio(self) -> None:
        validator = CitationValidator()
        retrieved = self._make_retrieved(
            [
                RetrievedSection(source="KP", label="Papers", content="Paper A."),
            ]
        )
        result = validator.validate(
            [
                {"paper_title": "Paper A", "relevance": "Yes"},
                {"paper_title": "Paper B", "relevance": "No"},
            ],
            retrieved,
        )
        assert result.success_ratio == 0.5

    def test_success_ratio_empty(self) -> None:
        validator = CitationValidator()
        result = validator.validate([], self._make_retrieved())
        assert result.success_ratio == 1.0


# ── ConfidenceCalibrator tests ─────────────────────────────────


class TestConfidenceCalibrator:
    def test_calibrate_empty_retrieval(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult()
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult([], [], 0, 0, 0)
        confidence = calibrator.calibrate(retrieved, cv)
        assert confidence == 0.1

    def test_calibrate_high_signal(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(
                    source="KP",
                    label="Findings",
                    content="Important findings here." * 50,
                    score=80.0,
                ),
                RetrievedSection(
                    source="Landscape", label="Methods", content="Various methods." * 30, score=60.0
                ),
            ],
            total_char_count=4000,
        )
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult(
            validated=[Citation(paper_title="Paper A")],
            discarded=[],
            total_examined=1,
            kept_count=1,
            discarded_count=0,
        )
        confidence = calibrator.calibrate(retrieved, cv, model_confidence=0.9)
        # Should be well above 0.5 with all positive signals
        assert confidence > 0.5
        assert confidence <= 1.0

    def test_calibrate_low_signal(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="Authors", content="John Smith.", score=0.0),
            ],
            total_char_count=11,
        )
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult([], [], 0, 0, 0)
        confidence = calibrator.calibrate(retrieved, cv, model_confidence=0.0)
        # Low evidence + no citations = low confidence
        assert 0.0 <= confidence <= 0.5

    def test_evidence_coverage_full(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="A", content="X", score=10.0),
                RetrievedSection(source="KP", label="B", content="Y", score=5.0),
            ]
        )
        assert calibrator._evidence_coverage(retrieved) == 1.0

    def test_evidence_coverage_partial(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="A", content="X", score=10.0),
                RetrievedSection(source="KP", label="B", content="Y", score=0.0),
            ]
        )
        assert calibrator._evidence_coverage(retrieved) == 0.5

    def test_evidence_coverage_empty(self) -> None:
        calibrator = ConfidenceCalibrator()
        assert calibrator._evidence_coverage(RetrievalResult()) == 0.0

    def test_context_completeness(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(total_char_count=12500)
        assert calibrator._context_completeness(retrieved, 25000) == 0.5

    def test_citation_count_score(self) -> None:
        calibrator = ConfidenceCalibrator()
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult(
            validated=[Citation()],
            discarded=[],
            total_examined=1,
            kept_count=1,
            discarded_count=0,
        )
        score = calibrator._citation_count_score(cv)
        assert 0 < score < 1.0

    def test_retrieval_score_avg(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="A", content="X", score=50.0),
                RetrievedSection(source="KP", label="B", content="Y", score=30.0),
            ]
        )
        score = calibrator._retrieval_score(retrieved)
        assert score == 0.4  # (50+30)/2/100

    def test_retrieval_score_no_positive(self) -> None:
        calibrator = ConfidenceCalibrator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="A", content="X", score=0.0),
            ]
        )
        assert calibrator._retrieval_score(retrieved) == 0.0

    def test_cap_model_confidence(self) -> None:
        calibrator = ConfidenceCalibrator()
        assert calibrator._cap_model_confidence(1.5) == 1.0
        assert calibrator._cap_model_confidence(-0.5) == 0.0
        assert calibrator._cap_model_confidence(0.7) == 0.7


# ── FollowUpGenerator tests ────────────────────────────────────


class TestFollowUpGenerator:
    def test_generate_from_methodologies(self) -> None:
        generator = FollowUpGenerator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(
                    source="KP", label="Methodologies", content="Deep Learning, Transformers, CNNs."
                ),
            ]
        )
        questions = generator.generate(retrieved)
        assert questions
        assert any("methodolog" in q.lower() for q in questions)

    def test_generate_from_technologies(self) -> None:
        generator = FollowUpGenerator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(
                    source="Landscape", label="Technologies", content="PyTorch, TensorFlow."
                ),
            ]
        )
        questions = generator.generate(retrieved)
        assert questions
        assert any("technolog" in q.lower() for q in questions)

    def test_generate_from_datasets(self) -> None:
        generator = FollowUpGenerator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="Landscape", label="Datasets", content="ImageNet, COCO."),
            ]
        )
        questions = generator.generate(retrieved)
        assert questions
        assert any("dataset" in q.lower() for q in questions)

    def test_generate_from_gaps(self) -> None:
        generator = FollowUpGenerator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(
                    source="Gap Report",
                    label="Research Gaps",
                    content="Missing multimodal benchmark.",
                ),
            ]
        )
        questions = generator.generate(retrieved)
        assert questions
        assert any("gap" in q.lower() or "challenge" in q.lower() for q in questions)

    def test_generate_no_duplicates(self) -> None:
        generator = FollowUpGenerator()
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="Methodologies", content="Deep Learning."),
                RetrievedSection(
                    source="Landscape", label="Methodologies", content="Deep Learning is popular."
                ),
            ]
        )
        questions = generator.generate(retrieved)
        assert len(questions) <= 5
        # Check for case-insensitive uniqueness
        normalized = [q.lower().strip() for q in questions]
        assert len(normalized) == len(set(normalized))

    def test_generate_empty_retrieval(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(RetrievalResult())
        assert isinstance(questions, list)

    def test_generate_respects_max(self) -> None:
        generator = FollowUpGenerator()
        sections = [
            RetrievedSection(source="KP", label=label, content="Content about " + label + ".")
            for label in [
                "Methodologies",
                "Technologies",
                "Datasets",
                "Research Gaps",
                "Limitations",
                "Future Work",
                "Applications",
                "Key Findings",
            ]
        ]
        retrieved = RetrievalResult(sections=sections)
        questions = generator.generate(retrieved)
        assert len(questions) <= 5

    def test_extract_topics(self) -> None:
        topics = FollowUpGenerator._extract_topics(
            "[Paper A] Key finding about transformers.\n[Paper B] Another finding about CNNs."
        )
        assert len(topics) > 0
        assert any("Key finding" in t for t in topics)

    def test_normalize_removes_punctuation(self) -> None:
        assert FollowUpGenerator._normalize("What methodologies?") == "whatmethodologies"
        assert FollowUpGenerator._normalize("What   methodologies!!!") == "whatmethodologies"

    def test_build_fallback_questions(self) -> None:
        retrieved = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="Key Findings", content="Finding 1."),
            ]
        )
        fallback = FollowUpGenerator._build_fallback_questions(retrieved)
        assert fallback
        assert any("finding" in q.lower() for q in fallback)
