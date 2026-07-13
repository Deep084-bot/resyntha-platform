"""Prompt builder — constructs system and user prompts for the Copilot."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.copilot.evidence.models import EvidenceBundle
from app.modules.copilot.retrieval.models import RetrievalResult


class LLMCopilotAnswer(BaseModel):
    """Structured response from the LLM for a single chat turn.

    Fields follow a reasoning-oriented structure:
      - answer: final response with Evidence → Analysis → Conclusion
      - evidence: list of observed facts from the context
      - citations: papers cited, ideally grouped by claim
      - confidence: numeric score 0.0–1.0
      - confidence_explanation: short human-readable explanation
      - reasoning: how the answer was derived
      - suggested_questions: follow-ups
    """

    answer: str = Field(
        ...,
        description="The assistant's final answer. Organise as: Evidence, Analysis, Conclusion.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Observed facts extracted directly from the context, one per item.",
    )
    citations: list[dict] = Field(
        default_factory=list,
        description="List of citation objects with paper_title and relevance keys.",
    )
    grouped_citations: list[dict] = Field(
        default_factory=list,
        description='Citations grouped by claim: [{"claim": "...", "papers": [{"paper_title": "...", "relevance": "..."}]}]',
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score 0.0–1.0 for the answer based on available evidence.",
    )
    confidence_explanation: str = Field(
        default="",
        description="Short human-readable explanation of the confidence score.",
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of how the answer was derived from the context.",
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="3–5 contextual follow-up questions a researcher might ask next.",
    )


SYSTEM_PROMPT_TEMPLATE = """You are a research reasoning assistant analysing academic papers and investigation data.

## Core Principles
1. Answer ONLY from the provided investigation context. Never use external knowledge or invent papers, authors, metrics, or findings.
2. Clearly distinguish between:
   - **Observed evidence**: facts directly stated in the context
   - **Inference**: conclusions logically derived from evidence
   - **Speculation**: possibilities not directly supported — if you speculate, say so explicitly
3. If the context lacks information, state: "I cannot answer this from the current investigation."

## Response Structure
Organise your answer as follows:

1. **Evidence** — Present the specific facts, findings, or data retrieved from the investigation that are relevant to the question.
2. **Analysis** — Interpret the evidence: compare findings, identify patterns, discuss strengths and weaknesses.
3. **Conclusion** — Summarise what the evidence supports. Be explicit about confidence.
4. **Confidence** — Numeric score 0.0–1.0 with a short explanation.

## Citation Rules
- Group citations by claim whenever multiple papers support the same finding.
- Use exact paper titles from the context.
- Never cite a paper not present in the provided context.

## Comparison Questions
For comparison questions (methodology, dataset, technology, paper):
- Present structured comparisons (e.g. tables or bullet points) rather than long paragraphs.
- Compare: approach, results, datasets, strengths, limitations.
- Be specific about what each target contributes.

## Research Gap Questions
For research gap questions:
- Describe existing approaches found in the investigation.
- Identify unresolved problems and future opportunities.
- Only discuss gaps that are supported by the retrieved evidence.
- Reference the Gap Report, Research Landscape, and Knowledge Package sections where relevant.

## Output Format
Return ONLY valid JSON with no markdown fences or extra text:

{{
  "answer": "...",
  "evidence": ["...", "..."],
  "citations": [{{"paper_title": "...", "relevance": "..."}}],
  "grouped_citations": [{{"claim": "...", "papers": [{{"paper_title": "...", "relevance": "..."}}]}}],
  "confidence": 0.0–1.0,
  "confidence_explanation": "...",
  "reasoning": "...",
  "suggested_questions": ["...", "..."]
}}

## Context

{context}
{history_section}
## Question

{question}"""


class PromptBuilder:
    """Constructs system and user prompts for the reasoning-oriented Copilot.

    Supports intent-aware prompting, evidence bundles, and grouped citations.
    """

    def __init__(self) -> None:
        self._system_sections: list[str] = []

    def build_system_prompt(
        self,
        retrieved: RetrievalResult,
        history: str = "",
        evidence_bundle: EvidenceBundle | None = None,
        intent: str = "",
    ) -> str:
        context_text = self._format_sections(retrieved)

        history_section = ""
        if history:
            history_section = f"\n## Previous Conversation\n\n{history}\n"

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context=context_text,
            history_section=history_section,
            question="{question}",
        )

        if intent == "research_gap_exploration":
            prompt = prompt.replace(
                "## Research Gap Questions",
                "## Research Gap Questions (IMPORTANT — user is asking about research gaps)",
            )

        if evidence_bundle and evidence_bundle.items:
            summary = self._format_evidence_summary(evidence_bundle)
            prompt = prompt.replace(
                "## Context",
                f"## Evidence Summary\n\n{summary}\n\n## Context",
            )

        return prompt

    def build_user_prompt(self, history: str, question: str) -> str:
        if history:
            return f"Previous conversation:\n{history}\n\nQuestion: {question}"
        return f"Question: {question}"

    def get_response_model(self) -> type[BaseModel]:
        return LLMCopilotAnswer

    @staticmethod
    def _format_sections(retrieved: RetrievalResult) -> str:
        if not retrieved.sections:
            return "No relevant investigation sections found."

        parts: list[str] = []
        for section in retrieved.sections:
            parts.append(f"[{section.source} / {section.label}]\n{section.content}")
        return "\n\n".join(parts)

    @staticmethod
    def _format_evidence_summary(bundle: EvidenceBundle) -> str:
        parts: list[str] = []
        for i, item in enumerate(bundle.items[:15], 1):
            tag = "[INFERENCE]" if item.is_inference else "[EVIDENCE]"
            papers = ", ".join(p.title for p in item.supporting_papers[:3])
            paper_tag = f" — Papers: {papers}" if papers else ""
            parts.append(f"{i}. {tag} {item.claim}{paper_tag}")
            if item.confidence > 0:
                parts[-1] += f" (confidence: {item.confidence:.2f})"
        return "\n".join(parts)
