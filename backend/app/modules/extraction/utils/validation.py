"""Validation utilities for extracted entities.

Provides:
- Empty entity rejection
- Malformed name detection
- Hallucination heuristics
- Confidence scoring for entities
"""

import re
from typing import Any

_RE_SINGLE_CHAR = re.compile(r"^[.,;:!?\-]$")
_RE_NUMERIC_ONLY = re.compile(r"^\d+[.\d]*$")
_RE_SPECIAL_ONLY = re.compile(r"^[^a-zA-Z0-9]+$")
_RE_PLACEHOLDER = re.compile(
    r"^(to be determined|tbd|n/a|na|unknown|none|not specified|"
    r"not available|not applicable|todo|placeholder|unclear|"
    r"not mentioned)$",
    re.IGNORECASE,
)
_MIN_NAME_LENGTH = 2
_MAX_NAME_LENGTH = 200


class ExtractionValidator:
    """Validate extracted entities and assign confidence scores."""

    @staticmethod
    def is_valid_entity_name(name: Any) -> bool:
        """Check if a name passes basic validity checks."""
        if not isinstance(name, str):
            return False
        cleaned = name.strip()
        if not cleaned:
            return False
        if len(cleaned) < _MIN_NAME_LENGTH:
            return False
        if len(cleaned) > _MAX_NAME_LENGTH:
            return False
        if _RE_SINGLE_CHAR.match(cleaned):
            return False
        if _RE_NUMERIC_ONLY.match(cleaned):
            return False
        if _RE_SPECIAL_ONLY.match(cleaned):
            return False
        if _RE_PLACEHOLDER.match(cleaned):
            return False
        return True

    @staticmethod
    def confidence_score(
        entity_type: str,
        name: str,
        has_extra_fields: bool = False,
    ) -> float:
        """Assign a confidence score (0.0–1.0) to an extracted entity.

        Scoring heuristic:
        - Entities with extra fields (e.g., department, country) get a
          bonus for being more complete.
        - Longer, more specific names score higher.
        - Placeholder/generic names score lower.
        """
        score = 0.5

        if not ExtractionValidator.is_valid_entity_name(name):
            return 0.0

        name_len = len(name.strip())

        if name_len >= 10:
            score += 0.2
        elif name_len >= 5:
            score += 0.1

        if entity_type == "author":
            if " " in name.strip():
                score += 0.15
            if len(name.split()) >= 2:
                score += 0.05
        elif entity_type == "institution":
            if any(
                t in name.lower() for t in ("university", "institute", "college", "lab", "school")
            ):
                score += 0.15
            score += 0.05
        elif entity_type == "dataset":
            if any(c.isupper() for c in name[1:]):
                score += 0.1
        elif entity_type == "technology":
            if any(c.isupper() for c in name[1:]):
                score += 0.1

        if has_extra_fields:
            score += 0.1

        return round(min(score, 1.0), 2)

    @staticmethod
    def filter_valid_entities(
        entities: list[Any],
        entity_type: str,
        name_key: str = "name",
        min_confidence: float = 0.3,
    ) -> list[dict]:
        """Filter a list of entities, returning only valid ones with
        scores attached.

        *entities* can be strings or dicts with a *name_key* field.
        Returns dicts with at least ``name`` and ``confidence`` keys.
        """
        result: list[dict] = []
        for entity in entities:
            if isinstance(entity, str):
                name = entity
                extra = False
            elif isinstance(entity, dict):
                name = entity.get(name_key, "")
                extra = len(entity) > 1
            else:
                continue

            if not ExtractionValidator.is_valid_entity_name(name):
                continue

            score = ExtractionValidator.confidence_score(entity_type, name, extra)
            if score < min_confidence:
                continue

            if isinstance(entity, dict):
                entry = dict(entity)
            else:
                entry = {"name": name}
            entry["confidence"] = score
            result.append(entry)

        return result
