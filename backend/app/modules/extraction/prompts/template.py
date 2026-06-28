"""Prompt template abstraction.

A ``PromptTemplate`` holds a text template with named placeholders
and provides a ``fill()`` method to substitute variables safely.
"""

from string import Template


class PromptTemplate:
    """Lightweight prompt template backed by string.Template.

    Usage::

        tmpl = PromptTemplate("Summarise: $text")
        result = tmpl.fill(text="Extracted knowledge is great.")
    """

    def __init__(self, template: str) -> None:
        self._template = Template(template)

    def fill(self, **kwargs: str) -> str:
        """Substitute variables and return the rendered prompt string."""
        return self._template.safe_substitute(**kwargs)
