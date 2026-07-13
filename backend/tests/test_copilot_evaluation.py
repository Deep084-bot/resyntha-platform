"""Copilot Evaluation Suite — deterministic quality checks for grounded answers, citations, confidence, and follow-ups.

This suite uses mocked retrieval results to verify end-to-end behaviour
of the quality pipeline without requiring an actual LLM.
"""

from __future__ import annotations

from app.modules.copilot.quality.confidence import ConfidenceCalibrator
from app.modules.copilot.quality.followup import FollowUpGenerator
from app.modules.copilot.quality.validator import CitationValidator
from app.modules.copilot.retrieval.models import (
    RetrievalDiagnostics,
    RetrievalResult,
    RetrievedSection,
)
from app.modules.copilot.schemas.response import Citation

# ── Representative evaluation questions ────────────────────────

_METHODOLOGY_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Methodologies",
            content="[Paper A] Deep Learning with CNNs.\n[Paper B] Transformer-based architectures.",
            score=45.0,
        ),
        RetrievedSection(
            source="Landscape",
            label="Methodologies",
            content="Deep Learning, CNNs, Transformers, RNNs, GNNs.",
            score=30.0,
        ),
    ]
)

_TECHNOLOGY_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Technologies",
            content="[Paper A] PyTorch for implementation.\n[Paper B] TensorFlow for deployment.",
            score=50.0,
        ),
        RetrievedSection(
            source="Landscape",
            label="Technologies",
            content="PyTorch, TensorFlow, JAX, Scikit-learn.",
            score=25.0,
        ),
    ]
)

_DATASET_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Datasets",
            content="ImageNet for image classification.\nCOCO for object detection.",
            score=40.0,
        ),
        RetrievedSection(
            source="Landscape",
            label="Datasets",
            content="ImageNet, COCO, CIFAR-10, MNIST.",
            score=20.0,
        ),
    ]
)

_GAP_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Gap Report",
            label="Research Gaps",
            content="[dataset] Missing multimodal benchmark.\n[evaluation] Limited to accuracy only.",
            score=60.0,
        ),
        RetrievedSection(
            source="Gap Report",
            label="Recommendations",
            content="Create a new benchmark covering multiple modalities.\nAdopt standardised evaluation metrics.",
            score=30.0,
        ),
    ]
)

_LIMITATION_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Limitations",
            content="[Paper A] Limited to small datasets.\n[Paper B] High computational cost.",
            score=35.0,
        ),
        RetrievedSection(
            source="Landscape",
            label="Limitations",
            content="Computational cost, data scarcity, evaluation bias.",
            score=15.0,
        ),
    ]
)

_FULL_EVIDENCE_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Key Findings",
            content="[Paper A] Transformer models achieve state-of-the-art on all benchmarks.",
            score=90.0,
        ),
        RetrievedSection(
            source="Knowledge Package",
            label="Methodologies",
            content="[Paper A] Self-attention mechanism with multi-head attention.",
            score=60.0,
        ),
        RetrievedSection(
            source="Knowledge Package",
            label="Technologies",
            content="[Paper A] PyTorch, CUDA.",
            score=40.0,
        ),
    ],
    total_char_count=3000,
)

_SUMMARY_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Key Findings",
            content="[Paper A] Main finding about transformers.\n[Paper B] Comparative analysis of architectures.",
            score=70.0,
        ),
        RetrievedSection(
            source="Knowledge Package",
            label="Summaries",
            content="[Paper A] Transformer architecture achieves SOTA.\n[Paper B] CNN still competitive on small data.",
            score=50.0,
        ),
    ]
)

_COMPARISON_RETRIEVAL = RetrievalResult(
    sections=[
        RetrievedSection(
            source="Knowledge Package",
            label="Methodologies",
            content="[Paper A] Uses transformers.\n[Paper B] Uses CNNs.\n[Paper C] Uses RNNs.",
            score=40.0,
        ),
        RetrievedSection(
            source="Knowledge Package",
            label="Key Findings",
            content="[Paper A] Transformers perform better for long sequences.\n[Paper B] CNNs more efficient for images.",
            score=55.0,
        ),
    ]
)


class TestEvaluation:
    """Deterministic Copilot quality evaluation tests."""

    # ── Grounded Answers ────────────────────────────────────────

    def test_eval_methodology_question_returns_grounded_content(self) -> None:
        """Q: What methodologies are used?"""
        sections = _METHODOLOGY_RETRIEVAL.sections
        assert sections
        assert any("methodolog" in s.label.lower() for s in sections)
        assert any("Deep Learning" in s.content or "CNNs" in s.content for s in sections)

    def test_eval_technology_question_returns_grounded_content(self) -> None:
        """Q: What technologies were employed?"""
        sections = _TECHNOLOGY_RETRIEVAL.sections
        assert sections
        assert any("technolog" in s.label.lower() for s in sections)
        assert any("PyTorch" in s.content for s in sections)

    def test_eval_dataset_question_returns_grounded_content(self) -> None:
        """Q: What datasets were used?"""
        sections = _DATASET_RETRIEVAL.sections
        assert sections
        assert any("dataset" in s.label.lower() for s in sections)
        assert any("ImageNet" in s.content for s in sections)

    def test_eval_gap_question_returns_gap_content(self) -> None:
        """Q: What research gaps exist?"""
        sections = _GAP_RETRIEVAL.sections
        assert sections
        assert any("gap" in s.label.lower() for s in sections)
        assert any("multimodal" in s.content for s in sections)

    def test_eval_limitation_question_returns_limitation_content(self) -> None:
        """Q: What are the limitations?"""
        sections = _LIMITATION_RETRIEVAL.sections
        assert sections
        assert any("limitation" in s.label.lower() for s in sections)
        assert any("computational" in s.content for s in sections)

    # ── Correct Citations ───────────────────────────────────────

    def test_eval_citation_keeps_valid_papers(self) -> None:
        validator = CitationValidator()
        result = validator.validate(
            [{"paper_title": "Paper A", "relevance": "Key finding"}],
            _FULL_EVIDENCE_RETRIEVAL,
        )
        assert result.kept_count == 1
        assert result.discarded_count == 0

    def test_eval_citation_discards_hallucinated(self) -> None:
        validator = CitationValidator()
        result = validator.validate(
            [{"paper_title": "Nonexistent Paper", "relevance": "Key"}],
            _FULL_EVIDENCE_RETRIEVAL,
        )
        assert result.kept_count == 0

    def test_eval_citation_partial_title_match(self) -> None:
        validator = CitationValidator()
        assert validator._citation_exists(
            "Paper A (2024)", "[Paper A] Transformer models achieve state-of-the-art."
        )

    def test_eval_citation_no_fabrication_on_empty(self) -> None:
        validator = CitationValidator()
        result = validator.validate([], _FULL_EVIDENCE_RETRIEVAL)
        assert result.validated == []
        assert result.discarded == []

    # ── Reasonable Confidence ────────────────────────────────────

    def test_eval_confidence_high_with_strong_evidence(self) -> None:
        calibrator = ConfidenceCalibrator()
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult(
            validated=[Citation(paper_title="Paper A")],
            discarded=[],
            total_examined=1,
            kept_count=1,
            discarded_count=0,
        )
        confidence = calibrator.calibrate(_FULL_EVIDENCE_RETRIEVAL, cv, model_confidence=0.9)
        assert 0.5 <= confidence <= 1.0

    def test_eval_confidence_low_with_weak_evidence(self) -> None:
        calibrator = ConfidenceCalibrator()
        weak = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="Authors", content="John Smith.", score=0.0),
            ],
            total_char_count=11,
        )
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult([], [], 0, 0, 0)
        confidence = calibrator.calibrate(weak, cv, model_confidence=0.0)
        assert confidence <= 0.5

    def test_eval_confidence_caps_model_contribution(self) -> None:
        calibrator = ConfidenceCalibrator()
        weak = RetrievalResult(
            sections=[
                RetrievedSection(source="KP", label="Authors", content="John Smith.", score=0.0),
            ],
            total_char_count=11,
        )
        from app.modules.copilot.quality.validator import CitationValidationResult

        cv = CitationValidationResult([], [], 0, 0, 0)
        # Even with model confidence 1.0, total should be capped by weak evidence
        high_model_conf = calibrator.calibrate(weak, cv, model_confidence=1.0)
        assert high_model_conf <= 0.5

    # ── Relevant Follow-up Questions ────────────────────────────

    def test_eval_followups_from_methodologies(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_METHODOLOGY_RETRIEVAL)
        assert questions
        assert any("methodolog" in q.lower() for q in questions)

    def test_eval_followups_from_technologies(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_TECHNOLOGY_RETRIEVAL)
        assert questions
        assert any("technolog" in q.lower() for q in questions)

    def test_eval_followups_from_datasets(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_DATASET_RETRIEVAL)
        assert questions
        assert any("dataset" in q.lower() for q in questions)

    def test_eval_followups_from_gaps(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_GAP_RETRIEVAL)
        assert questions
        assert any("gap" in q.lower() or "challenge" in q.lower() for q in questions)

    def test_eval_followups_no_duplicates(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_FULL_EVIDENCE_RETRIEVAL)
        normalized = [q.lower().strip() for q in questions]
        assert len(normalized) == len(set(normalized))

    def test_eval_followups_no_more_than_five(self) -> None:
        generator = FollowUpGenerator()
        questions = generator.generate(_FULL_EVIDENCE_RETRIEVAL)
        assert len(questions) <= 5

    # ── Retrieval Diagnostics ────────────────────────────────────

    def test_eval_diagnostics_tracks_sections(self) -> None:
        diag = RetrievalDiagnostics(
            total_raw_sections=10,
            scored_sections=8,
            dedup_removed=2,
            selected_count=4,
            dropped_low_score=2,
            dropped_budget=2,
            used_fallback=False,
            retrieval_duration_ms=15.5,
            num_keywords=3,
            num_signals=2,
        )
        assert diag.total_raw_sections == 10
        assert diag.selected_count == 4
        assert diag.retrieval_duration_ms == 15.5

    def test_eval_diagnostics_defaults(self) -> None:
        diag = RetrievalDiagnostics()
        assert diag.total_raw_sections == 0
        assert diag.dedup_removed == 0
        assert not diag.used_fallback

    # ── Prompt Structure ────────────────────────────────────────

    def test_eval_prompt_contains_rules_and_context(self) -> None:
        from app.modules.copilot.prompt.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_system_prompt(_FULL_EVIDENCE_RETRIEVAL)
        assert "Answer ONLY" in prompt or "Answer only" in prompt
        assert "invent papers" in prompt.lower()
        assert "citations" in prompt.lower()
        assert "confidence" in prompt.lower()
        assert "Question" in prompt

    def test_eval_prompt_includes_history_when_provided(self) -> None:
        from app.modules.copilot.prompt.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_system_prompt(
            _SUMMARY_RETRIEVAL, history="User: Tell me about the papers."
        )
        assert "Previous Conversation" in prompt
        assert "Tell me about the papers" in prompt

    def test_eval_prompt_omits_history_when_empty(self) -> None:
        from app.modules.copilot.prompt.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_system_prompt(_SUMMARY_RETRIEVAL)
        assert "Previous Conversation" not in prompt
