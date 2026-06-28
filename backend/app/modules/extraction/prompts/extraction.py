"""Extraction prompts for the knowledge extraction pipeline.

``EXTRACTION_SYSTEM_PROMPT`` defines the task and output schema.
``build_extraction_user_prompt()`` renders the paper context into a
user message.
"""

from app.modules.extraction.prompts.template import PromptTemplate

EXTRACTION_SYSTEM_PROMPT = """You are an expert research analyst.
Your task is to extract structured knowledge from academic papers.

Given a paper's metadata and text, return a JSON object with these fields:

- "research_questions": list of strings — key questions the paper addresses
- "key_findings": list of strings — main results or findings
- "methodology": string or null — research approach used
- "limitations": list of strings — acknowledged limitations
- "key_contributions": list of strings — novel contributions
- "relevant_techniques": list of strings — methods, tools, techniques
- "cited_works": list of strings — important works cited
- "future_work": list of strings — suggested future research
- "summary": string — concise one-paragraph summary

Return ONLY valid JSON. Do not include any text outside the JSON object.
If a field has no items, return an empty list. If methodology is not
applicable, return null.
"""

_USER_PROMPT_TEMPLATE = PromptTemplate(
    "Title: $title\n"
    "Authors: $authors\n"
    "Venue: $venue\n"
    "Year: $year\n"
    "DOI: $doi\n"
    "Abstract: $abstract\n"
)


def build_extraction_user_prompt(
    title: str,
    abstract: str = "",
    authors: str = "",
    venue: str = "",
    year: str = "",
    doi: str = "",
) -> str:
    """Build the user prompt for a single paper."""
    return _USER_PROMPT_TEMPLATE.fill(
        title=title,
        abstract=abstract,
        authors=authors,
        venue=venue,
        year=str(year),
        doi=doi,
    )
