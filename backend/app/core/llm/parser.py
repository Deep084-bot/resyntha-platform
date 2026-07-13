"""Provider-agnostic JSON parser for LLM responses.

LLMs often wrap JSON in markdown code fences, explanatory prose, or
leading/trailing whitespace.  This module provides a single entrypoint
that handles all common formatting variations before delegating to
``json.loads()``.

Usage::

    from app.core.llm.parser import parse_llm_json

    data = parse_llm_json(
        raw='```json\\n{"key": "value"}\\n```',
        finish_reason="stop",
    )
"""

import json
import re
from collections.abc import Mapping

from app.core.llm.exceptions import LLMParsingError
from app.observability.logger import get_logger

logger = get_logger(__name__)

_CODE_FENCE_PATTERN = re.compile(
    r"^[ \t]*```[a-zA-Z]*[ \t]*\n?(.*?)```[ \t]*$",
    re.DOTALL,
)


def _strip_code_fences(text: str) -> str:
    """Remove enclosing markdown code fences.

    Handles `` ```json``, `` ``` ``, and variants with leading whitespace.
    """
    match = _CODE_FENCE_PATTERN.match(text)
    if match:
        return match.group(1).strip()
    return text


def _find_json_object(text: str, start: int = 0) -> str | None:
    """Find a balanced JSON object ``{``…``}`` starting at or after *start*."""
    brace_start = text.find("{", start)
    if brace_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(brace_start, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == "\\" and in_string:
            escape = True
            continue

        if ch == '"' and not escape:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : i + 1]

    return None


def _find_json_array(text: str, start: int = 0) -> str | None:
    """Find a balanced JSON array ``[``…``]`` starting at or after *start*."""
    bracket_start = text.find("[", start)
    if bracket_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(bracket_start, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == "\\" and in_string:
            escape = True
            continue

        if ch == '"' and not escape:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[bracket_start : i + 1]

    return None


def parse_llm_json(
    raw: str,
    finish_reason: str | None = None,
) -> Mapping | list:
    """Parse an LLM response into a Python dict or list.

    The parser applies the following sanitisation steps in order:

    1. Strip leading/trailing whitespace.
    2. Remove enclosing markdown code fences.
    3. Try ``json.loads()`` directly on the sanitised result.
    4. Search for a balanced ``{``…``}`` or ``[``…``]`` and parse that.
    5. Raise ``LLMParsingError`` with full diagnostics.
    """
    stripped = raw.strip()
    sanitized = _strip_code_fences(stripped)

    for candidate in [sanitized, sanitized.strip()]:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue

    for extractor in [_find_json_object, _find_json_array]:
        parsed = extractor(sanitized)
        if parsed is not None:
            try:
                return json.loads(parsed)
            except (json.JSONDecodeError, ValueError):
                continue

    logger.error(
        "llm_json_parse_failed",
        raw_repr=repr(raw),
        raw_length=len(raw),
        sanitized_repr=repr(sanitized),
        sanitized_length=len(sanitized),
        finish_reason=finish_reason,
    )

    raise LLMParsingError(
        message=(
            f"Failed to parse LLM response as JSON after all sanitisation steps. "
            f"Raw length={len(raw)}, sanitized length={len(sanitized)}."
        ),
        raw=raw,
        sanitized=sanitized,
        finish_reason=finish_reason,
    )
