"""Intelligence presentation layer.

Renders a LandscapeResult into Markdown or JSON.
No graph traversal, no aggregation, no computation.
"""

from app.modules.intelligence.presentation.json import JsonRenderer
from app.modules.intelligence.presentation.markdown import MarkdownRenderer
from app.modules.intelligence.presentation.renderer import BaseRenderer

__all__ = [
    "BaseRenderer",
    "JsonRenderer",
    "MarkdownRenderer",
]
