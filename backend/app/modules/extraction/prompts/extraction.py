"""Extraction prompts for the knowledge extraction pipeline.

``EXTRACTION_SYSTEM_PROMPT`` defines the task and output schema.
``build_extraction_user_prompt()`` renders the paper context into a
user message.
"""

from app.modules.extraction.prompts.template import PromptTemplate

EXTRACTION_SYSTEM_PROMPT = """You are an expert research analyst.
Your task is to extract structured knowledge from academic papers.

Given a paper's metadata and text, return a JSON object with these fields:

─── Core fields ──────────────────────────────────────────────────
"research_questions": list of strings — key questions the paper addresses
"key_findings": list of strings — main results or findings
"methodology": string or null — primary research approach used
"limitations": list of strings — acknowledged limitations
"key_contributions": list of strings — novel contributions
"relevant_techniques": list of strings — methods, tools, techniques
"cited_works": list of strings — important works cited
"future_work": list of strings — suggested future research
"summary": string — concise one-paragraph summary

─── Authors ───────────────────────────────────────────────────────
"authors": list of objects with:
    "name": string — full author name (e.g. "John A. Smith")
    "order": number or null — 1-based position in author list
    "is_corresponding": boolean or null — whether this is the corresponding author

─── Affiliations ──────────────────────────────────────────────────
"institutions": list of objects with:
    "name": string — institution name (e.g. "Stanford University")
    "department": string or null — department or division
    "country": string or null — country of the institution

─── Datasets ──────────────────────────────────────────────────────
"datasets_used": list of objects with:
    "name": string — dataset name
    "is_public": boolean or null — whether the dataset is publicly available
    "is_benchmark": boolean or null — whether this is a benchmark dataset

─── Technologies ──────────────────────────────────────────────────
"technologies": list of objects with:
    "name": string — technology name (e.g. "PyTorch", "BERT", "k-means")
    "type": string or null — category: "framework", "model", "algorithm", "library"

─── Evaluation Metrics ────────────────────────────────────────────
"evaluation_metrics": list of objects with:
    "name": string — metric name (e.g. "accuracy", "F1", "BLEU")
    "value": string or null — reported value (e.g. "92.5%")
    "dataset": string or null — dataset on which the metric was measured

─── Additional fields ─────────────────────────────────────────────
"research_domains": list of strings — research domains or subfields
"keywords": list of strings — keywords or key phrases describing the paper
"paper_type": string or null — type: "survey", "benchmark", "application",
    "theory", "system", "dataset", "methodology", or null
"funding": string or null — funding information or grant acknowledgments

Return ONLY valid JSON. Do not include any text outside the JSON object.
If a field has no items, return an empty list. If a nullable field is not
applicable, return null. Be thorough but accurate — do not hallucinate
authors, datasets, or metrics that are not explicitly mentioned in the
paper text.
"""

_USER_PROMPT_TEMPLATE = PromptTemplate(
    "Title: $title\nAuthors: $authors\nVenue: $venue\nYear: $year\nDOI: $doi\nAbstract: $abstract\n"
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
