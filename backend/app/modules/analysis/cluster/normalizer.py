"""Text normalization utilities for clustering.

Performs simple deterministic transformations to group similar terms:
lowercasing, punctuation stripping, whitespace normalization, and
basic stemming/suffix stripping.
"""

import re
import unicodedata

_RE_WHITESPACE = re.compile(r"\s+")
_RE_PUNCTUATION = re.compile(r"[^\w\s-]")
_RE_TRAILING_STEM = re.compile(r"(ing|tion|ions|s|es|ed|ment|ments|al)$", re.IGNORECASE)


class Normalizer:
    """Lightweight text normalizer for clustering terms.

    All methods are pure functions exposed as classmethods for
    convenient composition.
    """

    @classmethod
    def normalize(cls, text: str) -> str:
        """Full normalization pipeline: strip → lowercase → stem."""
        cleaned = cls.strip_punctuation(cls.strip_whitespace(text))
        return cls.light_stem(cleaned.lower().strip())

    @staticmethod
    def strip_whitespace(text: str) -> str:
        """Collapse runs of whitespace into a single space."""
        return _RE_WHITESPACE.sub(" ", text).strip()

    @staticmethod
    def strip_punctuation(text: str) -> str:
        """Remove punctuation except hyphens."""
        return _RE_PUNCTUATION.sub(" ", text)

    @staticmethod
    def strip_accents(text: str) -> str:
        """Remove diacritics."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.category(c).startswith("M"))

    @staticmethod
    def light_stem(word: str) -> str:
        """Remove common English suffixes (very light stemming)."""
        return _RE_TRAILING_STEM.sub("", word)
