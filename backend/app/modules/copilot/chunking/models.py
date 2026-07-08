"""Chunk dataclass and associated types."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A single chunk of investigation content ready for embedding."""

    investigation_id: uuid.UUID
    artifact_id: uuid.UUID | None = None
    paper_id: uuid.UUID | None = None
    section: str = ""
    source: str = ""
    chunk_index: int = 0
    content: str = ""
    char_count: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.char_count = len(self.content)
