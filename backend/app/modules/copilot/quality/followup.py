"""Follow-up quality — generates contextual follow-up questions from evidence."""

from __future__ import annotations

import re

from app.modules.copilot.evidence.models import EvidenceBundle
from app.modules.copilot.retrieval.models import RetrievalResult

_INTERESTING_LABELS = {
    "methodologies",
    "technologies",
    "datasets",
    "evaluation metrics",
    "research gaps",
    "limitations",
    "future work",
    "research questions",
    "recommendations",
    "applications",
    "key findings",
}


class FollowUpGenerator:
    """Generates contextual follow-up questions from retrieved section labels and content.

    Strategies, in priority order:
      1. Direct label-based questions for methodology/technology/dataset/gap sections.
      2. Content-specific questions from key findings.
      3. Gap/future-work exploration questions.
      4. Evidence-bundle-aware questions when bundle is provided.
      5. Deduplication (case-insensitive).
    """

    _MAX_FOLLOW_UPS = 5

    _PREFIXES = {
        "methodologies": "What methodologies",
        "technologies": "What technologies",
        "datasets": "What datasets",
        "evaluation metrics": "What evaluation metrics",
        "research gaps": "What research gaps",
        "limitations": "What limitations",
        "future work": "What future work directions",
        "research questions": "What open research questions",
        "recommendations": "What recommendations",
        "applications": "What applications",
        "key findings": "What are the key findings",
    }

    _EVIDENCE_PREFIXES = {
        "methodology": "How do the methodologies compare",
        "dataset": "Which datasets are most commonly used",
        "limitation": "What are the main limitations shared across studies",
        "future": "What future research directions are suggested",
        "gap": "What research gaps remain unexplored",
    }

    def generate(
        self,
        retrieved: RetrievalResult | None = None,
        bundle: EvidenceBundle | None = None,
    ) -> list[str]:
        questions: list[str] = []
        seen: set[str] = set()

        if retrieved:
            for section in retrieved.sections:
                label_lower = section.label.strip().lower()
                if label_lower in self._PREFIXES:
                    prefix = self._PREFIXES[label_lower]
                    for q in self._build_label_questions(section, prefix):
                        normalized = self._normalize(q)
                        if normalized not in seen:
                            questions.append(q)
                            seen.add(normalized)
                if len(questions) >= self._MAX_FOLLOW_UPS:
                    break

        if bundle and bundle.items:
            topics = self._extract_bundle_topics(bundle)
            for topic in topics:
                prefix = self._EVIDENCE_PREFIXES.get(topic)
                if prefix is None:
                    continue
                q = f"{prefix} in these studies?"
                normalized = self._normalize(q)
                if normalized not in seen:
                    questions.append(q)
                    seen.add(normalized)
                if len(questions) >= self._MAX_FOLLOW_UPS:
                    break

        if len(questions) < self._MAX_FOLLOW_UPS:
            for q in self._build_fallback_questions(retrieved):
                normalized = self._normalize(q)
                if normalized not in seen:
                    questions.append(q)
                    seen.add(normalized)
                if len(questions) >= self._MAX_FOLLOW_UPS:
                    break

        return questions[: self._MAX_FOLLOW_UPS]

    def _build_label_questions(self, section, prefix: str) -> list[str]:
        topics = self._extract_topics(section.content, max_topics=3)
        if topics:
            return [f"{prefix} are most relevant to {', '.join(topics[:2])}?"]
        return [f"{prefix} are used in this research area?"]

    @staticmethod
    def _extract_topics(content: str, max_topics: int = 3) -> list[str]:
        lines = content.split("\n")
        topics: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^\[.*?\]\s*", "", line)
            line = re.sub(r"^[-•*]\s*", "", line)
            colon_idx = line.find(":")
            if colon_idx > 0:
                line = line[:colon_idx]
            if len(line) > 80:
                line = line[:80]
            line = line.strip()
            if line and len(line) > 5:
                topics.append(line)
                if len(topics) >= max_topics:
                    break
        return topics

    @staticmethod
    def _extract_bundle_topics(bundle: EvidenceBundle) -> list[str]:
        topics: list[str] = []
        seen_topics: set[str] = set()
        claim_text = " ".join(item.claim.lower() for item in bundle.items)

        for keyword, topic in [
            ("methodolog", "methodology"),
            ("dataset", "dataset"),
            ("limit", "limitation"),
            ("future", "future"),
            ("gap", "gap"),
        ]:
            if keyword in claim_text and topic not in seen_topics:
                topics.append(topic)
                seen_topics.add(topic)

        return topics

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower().strip())

    @staticmethod
    def _build_fallback_questions(retrieved: RetrievalResult | None) -> list[str]:
        candidates = [
            "Can you summarise the key findings?",
            "What conclusions can be drawn from this investigation?",
            "How do the methodologies compare across the reviewed papers?",
            "What are the main research challenges identified?",
            "What recommendations are suggested for future work?",
            "How were the datasets used in the reviewed studies?",
            "What technologies were employed in this research?",
        ]
        if retrieved is None or not retrieved.sections:
            return candidates[:3]
        seen_labels = {s.label.strip().lower() for s in retrieved.sections}
        relevant: list[str] = []
        for q in candidates:
            if "finding" in q and "key findings" in seen_labels:
                relevant.append(q)
            elif "methodolog" in q and "methodologies" in seen_labels:
                relevant.append(q)
            elif "dataset" in q and "datasets" in seen_labels:
                relevant.append(q)
            elif "technolog" in q and "technologies" in seen_labels:
                relevant.append(q)
            elif "challenge" in q and "limitations" in seen_labels:
                relevant.append(q)
            elif "recommendation" in q and "recommendations" in seen_labels:
                relevant.append(q)
        return relevant or candidates[:3]
