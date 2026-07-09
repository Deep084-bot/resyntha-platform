"""Tests for PromptBuilder and the LLMCopilotAnswer model."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from app.modules.copilot.prompt.builder import LLMCopilotAnswer, PromptBuilder


class TestLLMCopilotAnswer:
    def test_valid_answer(self) -> None:
        result = LLMCopilotAnswer(
            answer="The papers focus on transformer architectures.",
            citations=[{"paper_title": "Attention Is All You Need", "relevance": "Core reference"}],
            confidence=0.95,
            reasoning="Directly supported by the knowledge package.",
            suggested_questions=["What improvements have been proposed?"],
        )
        assert result.answer.startswith("The papers")
        assert len(result.citations) == 1
        assert result.suggested_questions[0] == "What improvements have been proposed?"

    def test_minimal_answer(self) -> None:
        result = LLMCopilotAnswer(answer="I cannot answer this from the current investigation.")
        assert result.citations == []
        assert result.suggested_questions == []
        assert result.confidence == 0.0

    def test_invalid_missing_answer(self) -> None:
        with pytest.raises(ValidationError):
            LLMCopilotAnswer()

    def test_suggested_questions_defaults_to_empty(self) -> None:
        result = LLMCopilotAnswer(answer="Test")
        assert result.suggested_questions == []

    def test_citations_accept_dicts(self) -> None:
        result = LLMCopilotAnswer(
            answer="Answer",
            citations=[
                {"paper_title": "Paper A", "relevance": "High"},
                {"paper_title": "Paper B", "relevance": "Medium"},
            ],
        )
        assert len(result.citations) == 2
        assert result.citations[0]["paper_title"] == "Paper A"
        assert result.citations[1]["paper_title"] == "Paper B"


class TestPromptBuilder:
    def _make_result(self, content: str = "Test context data") -> RetrievalResult:
        from app.modules.copilot.retrieval.models import RetrievalResult, RetrievedSection
        return RetrievalResult(sections=[
            RetrievedSection(source="Test", label="Data", content=content),
        ])

    def test_build_system_prompt_contains_context(self) -> None:
        builder = PromptBuilder()
        result = self._make_result("Test context data")
        prompt = builder.build_system_prompt(result)
        assert "Test context data" in prompt
        assert "research reasoning assistant" in prompt.lower()
        assert "Answer ONLY" in prompt or "answer only" in prompt.lower()
        assert "citations" in prompt.lower()
        assert "suggested_questions" in prompt

    def test_build_system_prompt_contains_rules(self) -> None:
        builder = PromptBuilder()
        result = self._make_result("Context")
        prompt = builder.build_system_prompt(result)
        assert "invent papers" in prompt.lower()
        assert "cannot answer" in prompt.lower()
        assert "citations" in prompt.lower()
        assert "confidence" in prompt.lower()

    def test_build_user_prompt_with_history(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(
            history="User: What is this about?\nAssistant: It's about ML.",
            question="Summarize the findings.",
        )
        assert "Previous conversation:" in prompt
        assert "What is this about?" in prompt
        assert "Summarize the findings." in prompt

    def test_build_user_prompt_without_history(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(history="", question="What are the key results?")
        assert "Previous conversation:" not in prompt
        assert "What are the key results?" in prompt

    def test_get_response_model_returns_llm_answer(self) -> None:
        builder = PromptBuilder()
        model = builder.get_response_model()
        assert model is LLMCopilotAnswer

    def test_build_system_prompt_contains_sections(self) -> None:
        builder = PromptBuilder()
        from app.modules.copilot.retrieval.models import RetrievalResult, RetrievedSection
        result = RetrievalResult(sections=[
            RetrievedSection(source="KP", label="Key Findings", content="Finding 1."),
        ])
        prompt = builder.build_system_prompt(result, history="User: test")
        assert "KP" in prompt
        assert "Key Findings" in prompt
        assert "Finding 1" in prompt
        assert "Previous Conversation" in prompt

    def test_build_system_prompt_no_history(self) -> None:
        builder = PromptBuilder()
        from app.modules.copilot.retrieval.models import RetrievalResult, RetrievedSection
        result = RetrievalResult(sections=[
            RetrievedSection(source="KP", label="Findings", content="Finding 1."),
        ])
        prompt = builder.build_system_prompt(result)
        assert "Previous Conversation" not in prompt

    def test_build_system_prompt_empty_sections(self) -> None:
        builder = PromptBuilder()
        from app.modules.copilot.retrieval.models import RetrievalResult
        prompt = builder.build_system_prompt(RetrievalResult())
        assert "No relevant investigation sections found" in prompt
