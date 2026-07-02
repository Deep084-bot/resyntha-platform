import json
import uuid

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.copilot.repository.repository import CopilotRepository
from app.modules.copilot.schemas.response import ChatResponse, Citation
from app.core.llm import BaseLLMProvider, ProviderFactory
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)


class LLMCitation(BaseModel):
    paper_title: str = ""
    relevance: str = ""


class LLMCopilotAnswer(BaseModel):
    answer: str
    citations: list[LLMCitation] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


class LLMSuggestedQuestions(BaseModel):
    questions: list[str] = Field(default_factory=list)


CONTEXT_CHAR_LIMIT = 30000


class CopilotService:
    def __init__(
        self,
        session: Session,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self._copilot_repo = CopilotRepository(session)
        self._paper_repo = PaperRepository(session)
        self._artifact_repo = ArtifactRepository(session)
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

        context = self._build_context(investigation_id)
        history = self._get_history(conversation.id)

        system_prompt = self._build_system_prompt(context)
        user_prompt = self._build_user_prompt(history, question)

        answer_result, usage = await self._llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=LLMCopilotAnswer,
            temperature=0.3,
            max_tokens=4096,
        )

        answer_citations = [
            Citation(
                paper_title=c.paper_title,
                paper_id="",
                relevance=c.relevance,
            )
            for c in answer_result.citations
        ]

        paper_id_map = self._build_paper_title_map(investigation_id)
        for citation in answer_citations:
            if citation.paper_title in paper_id_map:
                citation.paper_id = str(paper_id_map[citation.paper_title])

        questions_result = await self._generate_suggested_questions(context)

        message_metadata = {
            "citations": [c.model_dump() for c in answer_citations],
            "confidence": answer_result.confidence,
            "reasoning": answer_result.reasoning,
            "suggested_questions": questions_result.questions,
            "tokens_used": usage.total_tokens if usage else 0,
        }

        self._copilot_repo.add_message(
            conversation.id, "user", question
        )

        assistant_msg = self._copilot_repo.add_message(
            conversation.id,
            "assistant",
            answer_result.answer,
            metadata=message_metadata,
        )

        self._session.commit()

        return ChatResponse(
            answer=answer_result.answer,
            citations=answer_citations,
            confidence=answer_result.confidence,
            reasoning=answer_result.reasoning,
            suggested_questions=questions_result.questions,
            message_id=str(assistant_msg.id),
            conversation_id=str(conversation.id),
        )

    def _build_context(self, investigation_id: uuid.UUID) -> str:
        sections: list[str] = []

        papers = self._paper_repo.list_by_investigation(investigation_id)
        if papers:
            paper_lines = ["=== PAPERS ==="]
            for p in papers:
                abstract = (p.abstract or "")[:500]
                authors = ", ".join(getattr(p, "authors", []) or [])
                paper_lines.append(
                    f"Title: {p.title}\n"
                    f"Authors: {authors}\n"
                    f"Abstract: {abstract}\n"
                    f"DOI: {p.doi or 'N/A'}\n"
                )
            sections.append("\n".join(paper_lines))

        artifact_types = [
            "paper_collection",
            "validated_collection",
            "knowledge_package",
            "research_landscape",
            "research_gap_report",
        ]

        all_artifacts = self._artifact_repo.list_by_investigation(investigation_id)

        for atype in artifact_types:
            matches = [a for a in all_artifacts if a.artifact_type == atype]
            if not matches:
                continue
            artifact = max(matches, key=lambda a: a.created_at)
            if artifact.payload:
                payload_str = json.dumps(artifact.payload, indent=1)[:4000]
                label = atype.upper().replace("_", " ")
                sections.append(f"\n=== {label} ===\n{payload_str}")

        full_context = "\n\n".join(sections)

        if len(full_context) > CONTEXT_CHAR_LIMIT:
            full_context = full_context[:CONTEXT_CHAR_LIMIT]
            last_newline = full_context.rfind("\n")
            if last_newline > 0:
                full_context = full_context[:last_newline]
            full_context += "\n[Context truncated due to length]"

        return full_context

    def _get_history(self, conversation_id: uuid.UUID) -> str:
        messages = self._copilot_repo.get_messages(conversation_id)
        lines: list[str] = []
        for msg in messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{prefix}: {msg.content[:2000]}")
        return "\n".join(lines)

    def _build_system_prompt(self, context: str) -> str:
        return (
            "You are a research assistant analyzing academic papers and research data. "
            "Your answers must be based ONLY on the provided context. "
            "If you cannot answer the question from the context, say "
            "'I cannot answer this from the current investigation'. "
            "Cite specific papers by title when referencing their content. "
            "Return a JSON object with fields: "
            "answer (str), citations (list of objects with paper_title and relevance), "
            "confidence (float 0-1), reasoning (str).\n\n"
            f"CONTEXT:\n{context}"
        )

    def _build_user_prompt(
        self, history: str, question: str
    ) -> str:
        if history:
            return (
                f"Previous conversation:\n{history}\n\n"
                f"Question: {question}"
            )
        return question

    def _build_paper_title_map(
        self, investigation_id: uuid.UUID
    ) -> dict[str, str]:
        papers = self._paper_repo.list_by_investigation(investigation_id)
        return {p.title: str(p.id) for p in papers if p.title}

    async def _generate_suggested_questions(
        self, context: str
    ) -> LLMSuggestedQuestions:
        try:
            summary = context[:8000]
            system_prompt = (
                "Based on the following research context, generate 5 follow-up questions "
                "that a researcher might ask. Return them as a JSON object with a single "
                "field 'questions' containing an array of strings.\n\n"
                f"CONTEXT SUMMARY:\n{summary}"
            )
            result, _ = await self._llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt="Generate 5 follow-up questions based on the research context above.",
                response_model=LLMSuggestedQuestions,
                temperature=0.7,
                max_tokens=1024,
            )
            return result
        except Exception as exc:
            logger.warning("suggested_questions_failed", error=str(exc)[:200])
            return LLMSuggestedQuestions(
                questions=[
                    "What are the key findings across all papers?",
                    "What methodologies are most commonly used?",
                    "What research gaps were identified?",
                    "How do the papers compare in their approaches?",
                    "What future work is recommended?",
                ]
            )
