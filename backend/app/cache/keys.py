"""Centralized cache key generation.

Every cache key used in the application is built through a function in
this module so that key formats are never duplicated as string literals.
"""

from __future__ import annotations

import hashlib
import uuid


def investigation_key(investigation_id: uuid.UUID | str) -> str:
    return f"investigation:{investigation_id}"


def graph_key(investigation_id: uuid.UUID | str) -> str:
    return f"graph:{investigation_id}"


def landscape_key(investigation_id: uuid.UUID | str) -> str:
    return f"landscape:{investigation_id}"


def gap_report_key(investigation_id: uuid.UUID | str) -> str:
    return f"gap_report:{investigation_id}"


def knowledge_package_key(investigation_id: uuid.UUID | str) -> str:
    return f"knowledge_package:{investigation_id}"


def retrieval_key(investigation_id: uuid.UUID | str, question: str) -> str:
    h = hashlib.sha256(question.encode()).hexdigest()[:16]
    return f"retrieval:{investigation_id}:{h}"


def all_investigation_pattern(investigation_id: uuid.UUID | str) -> str:
    return f"*:{investigation_id}"
