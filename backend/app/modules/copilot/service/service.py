"""Copilot service — investigation-aware research assistant."""

import json
import time
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.core.llm import BaseLLMProvider, ProviderFactory
from app.core.llm.exceptions import LLMError, LLMParsingError
from app.modules.copilot.classification.classifier import QuestionClassifier
from app.modules.copilot.classification.models import QuestionAnalysis, QuestionIntent
from app.modules.copilot.evidence.aggregator import EvidenceAggregator
from app.modules.copilot.evidence.grouper import CitationGrouper
from app.modules.copilot.evidence.models import EvidenceBundle
from app.modules.copilot.prompt.builder import LLMCopilotAnswer, PromptBuilder
from app.modules.copilot.quality.confidence import ConfidenceCalibrator
from app.modules.copilot.quality.followup import FollowUpGenerator
from app.modules.copilot.quality.validator import CitationValidator
from app.modules.copilot.retrieval.models import RetrievalDiagnostics, RetrievalResult
from app.modules.copilot.retrieval.retriever import InvestigationRetriever
from app.modules.copilot.retrieval.semantic_retriever import SemanticRetriever
from app.modules.copilot.repository.repository import CopilotRepository
from app.modules.copilot.schemas.response import (
    ChatResponse,
    Citation,
    CopilotMessageResponse,
    StreamDone,
    StreamError,
    StreamToken,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)


_MALFORMED_ANSWER_PLACEHOLDER = "I encountered an issue processing the response. Please try rephrasing your question."


class _AnswerStreamExtractor:
    """Extracts the ``answer`` field value incrementally from a streaming JSON buffer.

    Improvements over the original:
    - Handles escaped quotes within the answer value.
    - Tolerates truncated unicode escape sequences at buffer boundary.
    - Resets internal state on detection of structural corruption.
    """

    def __init__(self) -> None:
        self._prev_len = 0
        self._reset_on_next = False

    def extract(self, buffer: str) -> str:
        current = self._parse_answer(buffer)
        if current is None:
            return ""
        new_text = current[self._prev_len:]
        if new_text and self._reset_on_next:
            self._reset_on_next = False
            # If we had a reset signal, start fresh but keep the last chunk
            self._prev_len = len(current)
            return new_text
        self._prev_len = len(current)
        return new_text

    def reset(self) -> None:
        self._prev_len = 0
        self._reset_on_next = False

    @staticmethod
    def _parse_answer(buffer: str) -> str | None:
        prefix = '"answer": "'
        idx = buffer.find(prefix)
        if idx == -1:
            return None
        start = idx + len(prefix)
        result: list[str] = []
        i = start
        while i < len(buffer):
            ch = buffer[i]
            if ch == '\\':
                if i + 1 < len(buffer):
                    next_ch = buffer[i + 1]
                    if next_ch == '"' or next_ch == '\\' or next_ch == '/':
                        result.append(next_ch)
                        i += 2
                    elif next_ch == 'n':
                        result.append('\n')
                        i += 2
                    elif next_ch == 't':
                        result.append('\t')
                        i += 2
                    elif next_ch == 'u':
                        # unicode escape — check if enough chars remain
                        if i + 5 < len(buffer):
                            try:
                                hex_str = buffer[i + 2:i + 6]
                                result.append(chr(int(hex_str, 16)))
                                i += 6
                            except (ValueError, IndexError):
                                result.append('?')
                                i += 1
                        else:
                            # truncated unicode at buffer boundary
                            break
                    else:
                        result.append(next_ch)
                        i += 2
                else:
                    break
            elif ch == '"':
                break
            elif ch == '\n' or ch == '\r':
                i += 1
            else:
                result.append(ch)
                i += 1
        return "".join(result)


class CopilotService:
    """Investigation-aware Copilot that grounds responses in investigation artifacts."""

    def __init__(
        self,
        session: Session,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self._copilot_repo = CopilotRepository(session)
        self._retriever = SemanticRetriever(session)
        self._fallback_retriever = InvestigationRetriever(session)
        self._classifier = QuestionClassifier()
        self._evidence_aggregator = EvidenceAggregator()
        self._citation_grouper = CitationGrouper()
        self._prompt_builder = PromptBuilder()
        self._citation_validator = CitationValidator()
        self._confidence_calibrator = ConfidenceCalibrator()
        self._followup_generator = FollowUpGenerator()
        self._session = session
        if llm_provider is not None:
            self._llm = llm_provider
        else:
            from app.config import get_settings
            self._llm = ProviderFactory.create(get_settings().LLM_PROVIDER)

    async def chat(
        self, investigation_id: uuid.UUID, question: str
    ) -> ChatResponse:
        conversation = self._copilot_repo.get_conversation_by_investigation(
            investigation_id
        )
        if conversation is None:
            conversation = self._copilot_repo.create_conversation(
                investigation_id
            )

        try:
            retrieved, analysis = self._retrieve_with_fallback(investigation_id, question)
        except Exception as exc:
            logger.error("copilot_retrieval_error", error=str(exc)[:500])
            return self._error_response("Failed to retrieve investigation context.")

        history = self._get_history_str(conversation.id)

        # Evidence aggregation
        evidence_bundle: EvidenceBundle | None = None
        try:
            paper_title_map = {s.content.split("Title: ")[-1].split("\n")[0]: s.content
                               for s in retrieved.sections if "Title:" in s.content} if retrieved.sections else None
            evidence_bundle = self._evidence_aggregator.aggregate(
                retrieved.sections, paper_title_map,
            )
            if retrieved.diagnostics is not None:
                retrieved.diagnostics.aggregated_evidence_count = len(evidence_bundle.items)
        except Exception as exc:
            logger.error("copilot_evidence_error", error=str(exc)[:500])

        # Citation grouping
        grouped_citations: list[dict] = []
        try:
            if evidence_bundle and evidence_bundle.items:
                grouped = self._citation_grouper.group(evidence_bundle)
                grouped_citations = [
                    {"claim": g.claim, "papers": [{"paper_title": p.title, "relevance": p.relevance} for p in g.papers]}
                    for g in grouped
                ]
                if retrieved.diagnostics is not None:
                    retrieved.diagnostics.grouped_citation_count = sum(len(g.papers) for g in grouped)
        except Exception as exc:
            logger.error("copilot_grouping_error", error=str(exc)[:500])

        try:
            system_prompt = self._prompt_builder.build_system_prompt(
                retrieved, history, evidence_bundle=evidence_bundle, intent=analysis.intent.value,
            ).replace("{question}", question)
            user_prompt = self._prompt_builder.build_user_prompt(history, question)
            if retrieved.diagnostics is not None:
                retrieved.diagnostics.estimated_prompt_chars = (
                    len(system_prompt) + len(user_prompt)
                )
                retrieved.diagnostics.comparison_mode = analysis.is_comparison
                retrieved.diagnostics.reasoning_mode = analysis.intent != QuestionIntent.GENERAL_RESEARCH_QUESTION
        except Exception as exc:
            logger.error("copilot_prompt_error", error=str(exc)[:500])
            return self._error_response("Failed to build prompt.")

        try:
            answer_result, usage = await self._llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=LLMCopilotAnswer,
                temperature=0.3,
                max_tokens=4096,
            )
        except LLMError as exc:
            logger.error("copilot_llm_error", error=str(exc)[:500])
            return self._error_response("The language model encountered an issue. Please try again.")
        except Exception as exc:
            logger.error("copilot_generation_error", error=str(exc)[:500])
            return self._error_response("An unexpected error occurred during generation.")

        citation_validation = self._citation_validator.validate(
            answer_result.citations, retrieved
        )
        validated_citations = citation_validation.validated

        calibrated_confidence, confidence_explanation = self._confidence_calibrator.calibrate_with_explanation(
            retrieved, citation_validation, answer_result.confidence
        )

        if retrieved.diagnostics is not None:
            retrieved.diagnostics.confidence_explanation = confidence_explanation

        followup_questions = self._followup_generator.generate(
            retrieved=retrieved, bundle=evidence_bundle,
        )

        if citation_validation.discarded:
            logger.info(
                "copilot_citations_discarded",
                discarded=citation_validation.discarded_count,
                total=citation_validation.total_examined,
            )

        message_metadata = {
            "citations": [c.model_dump() for c in validated_citations],
            "grouped_citations": grouped_citations,
            "confidence": calibrated_confidence,
            "confidence_explanation": confidence_explanation,
            "reasoning": answer_result.reasoning,
            "suggested_questions": followup_questions,
            "tokens_used": usage.total_tokens if usage else 0,
            "citation_validation": {
                "examined": citation_validation.total_examined,
                "kept": citation_validation.kept_count,
                "discarded": citation_validation.discarded_count,
            },
            "retrieval_diagnostics": self._serialize_diagnostics(retrieved.diagnostics),
            "detected_intent": analysis.intent.value,
            "evidence_count": len(evidence_bundle.items) if evidence_bundle else 0,
        }

        self._copilot_repo.add_message(conversation.id, "user", question)
        assistant_msg = self._copilot_repo.add_message(
            conversation.id,
            "assistant",
            answer_result.answer,
            metadata=message_metadata,
        )
        self._session.commit()

        return ChatResponse(
            answer=answer_result.answer,
            citations=validated_citations,
            confidence=calibrated_confidence,
            reasoning=answer_result.reasoning,
            suggested_questions=followup_questions,
            message_id=str(assistant_msg.id),
            conversation_id=str(conversation.id),
        )

    async def chat_stream(
        self, investigation_id: uuid.UUID, question: str
    ) -> AsyncIterator[StreamToken | StreamDone | StreamError]:
        conversation = self._copilot_repo.get_conversation_by_investigation(
            investigation_id
        )
        if conversation is None:
            conversation = self._copilot_repo.create_conversation(
                investigation_id
            )

        history = self._get_history_str(conversation.id)

        try:
            retrieved, analysis = self._retrieve_with_fallback(investigation_id, question)
        except Exception as exc:
            logger.error("copilot_retrieval_error", error=str(exc)[:500])
            yield StreamError(message="Failed to retrieve investigation context.")
            return

        # Evidence aggregation
        evidence_bundle: EvidenceBundle | None = None
        try:
            evidence_bundle = self._evidence_aggregator.aggregate(retrieved.sections)
            if retrieved.diagnostics is not None:
                retrieved.diagnostics.aggregated_evidence_count = len(evidence_bundle.items) if evidence_bundle else 0
        except Exception as exc:
            logger.error("copilot_evidence_error", error=str(exc)[:500])

        try:
            system_prompt = self._prompt_builder.build_system_prompt(
                retrieved, history, evidence_bundle=evidence_bundle, intent=analysis.intent.value,
            ).replace("{question}", question)
            user_prompt = self._prompt_builder.build_user_prompt(history, question)
            if retrieved.diagnostics is not None:
                retrieved.diagnostics.estimated_prompt_chars = (
                    len(system_prompt) + len(user_prompt)
                )
                retrieved.diagnostics.detected_intent = analysis.intent.value
                retrieved.diagnostics.comparison_mode = analysis.is_comparison
                retrieved.diagnostics.reasoning_mode = analysis.intent != QuestionIntent.GENERAL_RESEARCH_QUESTION
        except Exception as exc:
            logger.error("copilot_prompt_error", error=str(exc)[:500])
            yield StreamError(message="Failed to build prompt.")
            return

        extractor = _AnswerStreamExtractor()
        buffer = ""
        full_answer = ""

        try:
            async for token in self._llm.generate_stream(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=4096,
            ):
                buffer += token
                content = extractor.extract(buffer)
                if content:
                    full_answer += content
                    yield StreamToken(content=content)

        except LLMError as exc:
            logger.error("copilot_stream_llm_error", error=str(exc)[:500])
            yield StreamError(message="The language model encountered an issue. Please try again.")
            return
        except Exception as exc:
            logger.error("copilot_stream_error", error=str(exc)[:500])
            yield StreamError(message="A streaming error occurred. Please try again.")
            return

        parsed = self._try_parse_json(buffer)

        if parsed is None:
            if full_answer:
                answer_text = full_answer
                citations: list[Citation] = []
                confidence = 0.1
                confidence_explanation = "No structured response available."
                reasoning = ""
                suggested_questions: list[str] = []
            else:
                yield StreamError(message="Failed to parse assistant response.")
                return
        else:
            answer_text = parsed.get("answer") or full_answer or ""
            citation_validation = self._citation_validator.validate(
                parsed.get("citations", []), retrieved
            )
            citations = citation_validation.validated
            calibrated, confidence_explanation = self._confidence_calibrator.calibrate_with_explanation(
                retrieved, citation_validation, float(parsed.get("confidence", 0.0))
            )
            suggested_questions = self._followup_generator.generate(
                retrieved=retrieved, bundle=evidence_bundle,
            )
            confidence = calibrated
            reasoning = str(parsed.get("reasoning", ""))

            if retrieved.diagnostics is not None:
                retrieved.diagnostics.confidence_explanation = confidence_explanation

            if citation_validation.discarded:
                logger.info(
                    "copilot_stream_citations_discarded",
                    discarded=citation_validation.discarded_count,
                    total=citation_validation.total_examined,
                )

        message_metadata = {
            "citations": [
                {"paper_title": c.paper_title, "paper_id": c.paper_id, "relevance": c.relevance}
                for c in citations
            ],
            "confidence": confidence,
            "confidence_explanation": confidence_explanation,
            "reasoning": reasoning,
            "suggested_questions": suggested_questions,
            "retrieval_diagnostics": self._serialize_diagnostics(retrieved.diagnostics),
            "detected_intent": analysis.intent.value,
        }

        self._copilot_repo.add_message(conversation.id, "user", question)
        assistant_msg = self._copilot_repo.add_message(
            conversation.id,
            "assistant",
            full_answer or answer_text,
            metadata=message_metadata,
        )
        self._session.commit()

        yield StreamDone(
            message_id=str(assistant_msg.id),
            conversation_id=str(conversation.id),
            citations=citations,
            suggested_questions=suggested_questions,
            confidence=confidence,
            reasoning=reasoning,
        )

    def get_history(self, investigation_id: uuid.UUID) -> list[CopilotMessageResponse]:
        conversation = self._copilot_repo.get_conversation_by_investigation(
            investigation_id
        )
        if conversation is None:
            return []
        return [
            self._serialize_message(message)
            for message in self._copilot_repo.get_messages(conversation.id)
        ]

    # ── Internal helpers ────────────────────────────────────────

    def _retrieve_with_fallback(
        self,
        investigation_id: uuid.UUID,
        question: str,
    ) -> tuple[RetrievalResult, QuestionAnalysis]:
        """Classify question, then try semantic retriever; fall back to heuristic."""
        analysis = self._classifier.classify(question)

        try:
            result = self._retriever.retrieve(
                investigation_id, question, intent=analysis.intent,
            )
            if result.sections:
                if result.diagnostics is not None:
                    result.diagnostics.detected_intent = analysis.intent.value
                return result, analysis
            reason = result.metadata[0] if result.metadata else "empty_result"
        except Exception as exc:
            logger.error("copilot_semantic_error", error=str(exc)[:500])
            reason = str(exc)[:200]

        logger.info(
            "copilot_semantic_fallback",
            investigation_id=str(investigation_id),
            reason=reason,
        )
        fallback_result = self._fallback_retriever.retrieve(investigation_id, question)
        if fallback_result.diagnostics is not None:
            fallback_result.diagnostics.retriever_type = "heuristic"
            fallback_result.diagnostics.detected_intent = analysis.intent.value
        return fallback_result, analysis

    def _get_history_str(self, conversation_id: uuid.UUID) -> str:
        messages = self._copilot_repo.get_messages(conversation_id)
        lines: list[str] = []
        for msg in messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{prefix}: {msg.content[:2000]}")
        return "\n".join(lines)

    def _build_citations(
        self,
        raw_citations: list[dict],
        _paper_title_map: dict[str, str],  # kept for backwards compat
    ) -> list[Citation]:
        result: list[Citation] = []
        for c in raw_citations:
            title = c.get("paper_title", "") if isinstance(c, dict) else ""
            relevance = c.get("relevance", "") if isinstance(c, dict) else ""
            result.append(
                Citation(
                    paper_title=title,
                    paper_id="",
                    relevance=str(relevance),
                )
            )
        return result

    def _try_parse_json(self, buffer: str) -> dict | None:
        """Attempt to parse JSON from the buffer, handling common issues."""
        if not buffer:
            return None

        text = buffer.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Try stripping markdown fences
        for fence in ("```json", "```", "'''"):
            if fence in text:
                parts = text.split(fence)
                for part in parts:
                    part = part.strip()
                    if part.startswith('{'):
                        end_idx = part.rfind('}')
                        if end_idx != -1:
                            try:
                                return json.loads(part[:end_idx + 1])
                            except json.JSONDecodeError:
                                pass

        return None

    def _serialize_diagnostics(
        self, diagnostics: RetrievalDiagnostics | None
    ) -> dict:
        if diagnostics is None:
            return {}
        return {
            "total_raw_sections": diagnostics.total_raw_sections,
            "scored_sections": diagnostics.scored_sections,
            "dedup_removed": diagnostics.dedup_removed,
            "selected_count": diagnostics.selected_count,
            "dropped_low_score": diagnostics.dropped_low_score,
            "dropped_budget": diagnostics.dropped_budget,
            "truncated_count": diagnostics.truncated_count,
            "used_fallback": diagnostics.used_fallback,
            "budget_limit": diagnostics.budget_limit,
            "retrieval_duration_ms": round(diagnostics.retrieval_duration_ms, 2),
            "num_keywords": diagnostics.num_keywords,
            "num_signals": diagnostics.num_signals,
            "retriever_type": diagnostics.retriever_type,
            "estimated_prompt_chars": diagnostics.estimated_prompt_chars,
            "detected_intent": diagnostics.detected_intent,
            "aggregated_evidence_count": diagnostics.aggregated_evidence_count,
            "comparison_mode": diagnostics.comparison_mode,
            "reasoning_mode": diagnostics.reasoning_mode,
            "grouped_citation_count": diagnostics.grouped_citation_count,
            "confidence_explanation": diagnostics.confidence_explanation,
        }

    def _error_response(self, message: str) -> ChatResponse:
        return ChatResponse(
            answer=message,
            citations=[],
            confidence=0.0,
            reasoning="",
            suggested_questions=[],
            message_id="",
            conversation_id="",
        )

    def _serialize_message(self, message: object) -> CopilotMessageResponse:
        metadata = getattr(message, "_metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}

        raw_citations = metadata.get("citations") or metadata.get("sources") or []
        citations: list[Citation] = []
        if isinstance(raw_citations, list):
            for raw_citation in raw_citations:
                if not isinstance(raw_citation, dict):
                    continue
                citations.append(
                    Citation(
                        paper_title=str(raw_citation.get("paper_title", "") or ""),
                        paper_id=str(raw_citation.get("paper_id", "") or ""),
                        relevance=str(raw_citation.get("relevance", "") or ""),
                    )
                )

        raw_questions = metadata.get("suggested_questions") or []
        suggested_questions = [
            str(q) for q in raw_questions if isinstance(q, str)
        ]

        created_at = getattr(message, "created_at", None)
        created_at_value = created_at.isoformat() if created_at is not None else ""

        return CopilotMessageResponse(
            id=str(getattr(message, "id")),
            role=str(getattr(message, "role")),
            content=str(getattr(message, "content")),
            sources=citations,
            suggested_questions=suggested_questions,
            created_at=created_at_value,
        )
