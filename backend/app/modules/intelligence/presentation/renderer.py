from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.modules.intelligence.aggregation.models import LandscapeResult


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, landscape: LandscapeResult) -> Any:
        ...
