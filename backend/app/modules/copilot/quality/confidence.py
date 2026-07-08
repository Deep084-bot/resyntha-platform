"""Confidence calibration — combines multiple signals into a final confidence score."""

from __future__ import annotations

from app.modules.copilot.retrieval.models import RetrievalResult
from app.modules.copilot.quality.validator import CitationValidationResult


MAX_CHARS_DEFAULT = 25000


class ConfidenceCalibrator:
    """Calibrates confidence using multiple evidence signals.

    Signals used (each normalised to 0.0-1.0):
      - evidence_coverage:    ratio of retrieved sections with score > 0
      - context_completeness: char count / max budget
      - citation_validation:  kept / total citations
      - citation_count:       sigmoid-scaled citation count
      - retrieval_score:      average score of selected sections
      - model_confidence:     raw model confidence (capped to max 30 % contribution)
    """

    _MODEL_WEIGHT = 0.30
    _EVIDENCE_WEIGHT = 0.25
    _COMPLETENESS_WEIGHT = 0.10
    _CITATION_VALIDATION_WEIGHT = 0.15
    _CITATION_COUNT_WEIGHT = 0.05
    _RETRIEVAL_SCORE_WEIGHT = 0.15

    def calibrate(
        self,
        retrieved: RetrievalResult,
        citation_validation: CitationValidationResult,
        model_confidence: float = 0.0,
        max_chars: int = MAX_CHARS_DEFAULT,
    ) -> float:
        if not retrieved.sections:
            return 0.1

        evidence = self._evidence_coverage(retrieved)
        completeness = self._context_completeness(retrieved, max_chars)
        citation_val = self._citation_validation_score(citation_validation)
        citation_count = self._citation_count_score(citation_validation)
        retrieval = self._retrieval_score(retrieved)
        model = self._cap_model_confidence(model_confidence)

        score = (
            evidence * self._EVIDENCE_WEIGHT +
            completeness * self._COMPLETENESS_WEIGHT +
            citation_val * self._CITATION_VALIDATION_WEIGHT +
            citation_count * self._CITATION_COUNT_WEIGHT +
            retrieval * self._RETRIEVAL_SCORE_WEIGHT +
            model * self._MODEL_WEIGHT
        )

        return round(min(max(score, 0.0), 1.0), 2)

    @staticmethod
    def _evidence_coverage(retrieved: RetrievalResult) -> float:
        if not retrieved.sections:
            return 0.0
        positive = sum(1 for s in retrieved.sections if s.score > 0)
        return positive / len(retrieved.sections)

    @staticmethod
    def _context_completeness(retrieved: RetrievalResult, max_chars: int) -> float:
        if max_chars <= 0:
            return 0.0
        return min(retrieved.total_char_count / max_chars, 1.0)

    @staticmethod
    def _citation_validation_score(result: CitationValidationResult) -> float:
        return result.success_ratio

    @staticmethod
    def _citation_count_score(result: CitationValidationResult) -> float:
        count = result.kept_count
        return count / (count + 3.0)

    @staticmethod
    def _retrieval_score(retrieved: RetrievalResult) -> float:
        if not retrieved.sections:
            return 0.0
        scores = [s.score for s in retrieved.sections if s.score > 0]
        if not scores:
            return 0.0
        avg = sum(scores) / len(scores)
        return min(avg / 100.0, 1.0)

    @staticmethod
    def _cap_model_confidence(raw: float) -> float:
        return min(max(raw, 0.0), 1.0)
