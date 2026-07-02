"""Unit tests for ``parse_llm_json()``.

Covers every scenario described in the LLM output format specification:
  - bare JSON object
  - leading / trailing whitespace
  - markdown code fences (```````json````, ``````````
  - language-annotated fences (```````python````, `````````)
  - fences with leading whitespace
  - explanatory text before / after the JSON
  - JSON arrays
  - empty / whitespace-only input
  - invalid JSON
  - deeply nested objects with strings containing braces
"""

import json
import pytest
from app.core.llm.parser import parse_llm_json

from app.core.llm.exceptions import LLMParsingError


# ── Helpers ──────────────────────────────────────────────────────────

SAMPLE_DICT = {"key": "value", "number": 42, "nested": {"a": 1}}
SAMPLE_DICT_STR = json.dumps(SAMPLE_DICT)
SAMPLE_ARRAY = [1, 2, {"three": 3}]
SAMPLE_ARRAY_STR = json.dumps(SAMPLE_ARRAY)


# ── Case 1: bare JSON object ─────────────────────────────────────────

class TestBareJson:
    def test_bare_object(self) -> None:
        assert parse_llm_json(SAMPLE_DICT_STR) == SAMPLE_DICT

    def test_bare_array(self) -> None:
        assert parse_llm_json(SAMPLE_ARRAY_STR) == SAMPLE_ARRAY

    def test_bare_object_with_nested(self) -> None:
        raw = '{"outer": {"inner": 1, "list": [2, 3]}}'
        expected = {"outer": {"inner": 1, "list": [2, 3]}}
        assert parse_llm_json(raw) == expected


# ── Case 2: leading / trailing whitespace ────────────────────────────

class TestWhitespace:
    def test_leading_newline(self) -> None:
        assert parse_llm_json(f"\n{SAMPLE_DICT_STR}") == SAMPLE_DICT

    def test_trailing_newline(self) -> None:
        assert parse_llm_json(f"{SAMPLE_DICT_STR}\n") == SAMPLE_DICT

    def test_surrounding_newlines(self) -> None:
        assert parse_llm_json(f"\n\n{SAMPLE_DICT_STR}\n\n") == SAMPLE_DICT

    def test_spaces_and_tabs(self) -> None:
        assert parse_llm_json(f"  \t {SAMPLE_DICT_STR} \t  ") == SAMPLE_DICT

    def test_only_whitespace(self) -> None:
        with pytest.raises(LLMParsingError):
            parse_llm_json("   \n\n   ")


# ── Case 3: markdown code fences ─────────────────────────────────────

class TestCodeFences:
    def test_fenced_json(self) -> None:
        raw = f"```json\n{SAMPLE_DICT_STR}\n```"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_fenced_no_language(self) -> None:
        raw = f"```\n{SAMPLE_DICT_STR}\n```"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_fenced_other_language(self) -> None:
        raw = f"```python\n{SAMPLE_DICT_STR}\n```"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_fenced_with_leading_whitespace(self) -> None:
        raw = f"  ```json\n{SAMPLE_DICT_STR}\n  ```"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_fenced_inline(self) -> None:
        raw = f"```json {SAMPLE_DICT_STR} ```"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_fenced_array(self) -> None:
        raw = f"```json\n{SAMPLE_ARRAY_STR}\n```"
        assert parse_llm_json(raw) == SAMPLE_ARRAY


# ── Case 4 & 5: explanatory text around JSON ─────────────────────────

class TestExplanatoryText:
    def test_text_before_json(self) -> None:
        raw = f"Here is the JSON:\n{SAMPLE_DICT_STR}"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_text_after_json(self) -> None:
        raw = f"{SAMPLE_DICT_STR}\nThat's all folks."
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_text_before_and_after(self) -> None:
        raw = f"Explanation:\n{SAMPLE_DICT_STR}\nHope this helps!"
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_text_before_fenced(self) -> None:
        raw = f"Sure!\n```json\n{SAMPLE_DICT_STR}\n```\nLet me know."
        assert parse_llm_json(raw) == SAMPLE_DICT

    def test_multiline_prose(self) -> None:
        raw = (
            "Based on my analysis, here are the results:\n\n"
            "The JSON is:\n"
            f"```json\n{SAMPLE_DICT_STR}\n```\n\n"
            "Let me know if you need clarification."
        )
        assert parse_llm_json(raw) == SAMPLE_DICT


# ── Deeply nested JSON with tricky strings ───────────────────────────

class TestNestedAndStrings:
    NESTED = {
        "level1": {
            "level2": {
                "level3": {
                    "key": "value with {braces} and [brackets]",
                    "escape": 'quotes \\" inside',
                }
            }
        }
    }

    def test_deeply_nested(self) -> None:
        raw = json.dumps(self.NESTED)
        assert parse_llm_json(raw) == self.NESTED

    def test_nested_with_braces_in_strings(self) -> None:
        raw = '{"data": "text with { and } characters"}'
        assert parse_llm_json(raw) == {"data": "text with { and } characters"}

    def test_strings_with_escaped_quotes(self) -> None:
        raw = '{"msg": "he said \\"hello\\""}'
        assert parse_llm_json(raw) == {"msg": 'he said "hello"'}


# ── Error cases ──────────────────────────────────────────────────────

class TestErrorCases:
    def test_empty_string(self) -> None:
        with pytest.raises(LLMParsingError) as exc_info:
            parse_llm_json("")
        assert exc_info.value.raw == ""

    def test_invalid_json(self) -> None:
        with pytest.raises(LLMParsingError) as exc_info:
            parse_llm_json("not json at all")
        assert exc_info.value.finish_reason is None

    def test_broken_json(self) -> None:
        with pytest.raises(LLMParsingError):
            parse_llm_json('{"key": "value"')  # missing close brace

    def test_html_instead_of_json(self) -> None:
        with pytest.raises(LLMParsingError):
            parse_llm_json("<html><body>Hello</body></html>")

    def test_finish_reason_in_exception(self) -> None:
        with pytest.raises(LLMParsingError) as exc_info:
            parse_llm_json("invalid", finish_reason="stop")
        assert exc_info.value.finish_reason == "stop"
        assert exc_info.value.raw == "invalid"


# ── Return type ──────────────────────────────────────────────────────

class TestReturnType:
    def test_returns_dict(self) -> None:
        result = parse_llm_json('{"a": 1}')
        assert isinstance(result, dict)

    def test_returns_list(self) -> None:
        result = parse_llm_json("[1, 2, 3]")
        assert isinstance(result, list)
