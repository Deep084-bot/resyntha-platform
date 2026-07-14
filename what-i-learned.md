# What I Learned

## What I knew before starting

- Python/TypeScript, FastAPI basics, SQLAlchemy, React, Postgres
- REST API design patterns, repository/service layering
- Basic git workflows — feature branches, merge commits

## New concepts learned

- **Structured logging** — I'd never used structlog before. Designing log events as machine-parseable key-value pairs (snake_case event names) forced me to think about what information downstream consumers actually need. The logger factory indirection (`get_logger()` vs direct structlog calls) is there because I learned that you want a single point to inject correlation IDs later.
- **ARQ job queues with Redis** — Managing async background workers that can crash midway. The pipeline runner had to handle stages that succeed partially, retry transient failures, and surface progress to the frontend via polling. The `RetryExceededException` and `StageExecutionException` hierarchy came from hitting cases where a stage silently failed and the worker just hung.
- **Hybrid search scoring** — Semantic similarity alone doesn't work well for copilot-style Q&A. The `HybridScorer` with tunable weights (0.7 semantic, 0.3 keyword boost) was my first attempt at fusing vector and keyword signals. The keyword scoring itself has 7-8 signal types (methodology, dataset, domain, etc.) because I found that flat keyword overlap wasn't precise enough.
- **Duplicate resolution strategies** — Papers from different providers have the same content but no shared identifier. DOI is obvious. External IDs (arXiv, Semantic Scholar) catch some edge cases. Normalized title matching catches the rest. But every strategy has false positives (especially short generic titles), and the only fix is layering multiple checks and tracking provenance per field so you can audit decisions later.

## Mistakes made

- **API contract mismatch between backend and frontend** — Commit `1c068c2`. The artifact builder stored extraction results as a top-level list, but the Pydantic schema required a `dict`. This HTTP-500'd 5 frontend pages simultaneously. The frontend already had an `Array.isArray()` workaround, meaning I shipped two incompatible assumptions about the same data shape. The fix required an in-place DB migration for existing rows.
- **Frontend empty placeholder files** — `empty.ts` in 4 directories (`features/`, `services/`, `hooks/`, `types/`). These stubs are a signal I started building frontend structure before the backend was ready and never cleaned up. They solved no real problem.
- **Logging module as a TODO** — `app/config/logging.py` contains nothing but a docstring saying "TODO (Sprint 1)". Structlog is imported directly everywhere via `get_logger()` from the observability module, so this file is dead weight. I created a placeholder structure but never filled it in.
- **NotImplementedError stubs** — `SimilarityService` defines three methods (`paper_distance`, `most_similar`, `outlier_scores`) that all raise `NotImplementedError`. The class is instantiated but cannot be used. I committed an incomplete interface without wiring it to anything.
- **Multiple pipeline failure types** — Early commits (`9c5d2dd Fixed pipeline`, `586ca50 Pipeline improved`, `e00cc39 fix: improve pipeline retries`) suggest I broke and unfixed the same pipeline multiple times. The root cause was handling retries and partial failures inconsistently — some stages caught exceptions, others didn't.
- **git stash pollution** — Two stash commits (`e0e081c`, `c4c1c2a`) in the history that reference "WIP on main: Fixed bugs". Not terrible, but they clutter what would otherwise be a clean linear history.

## Interesting bugs

- **KNOWLEDGE_PACKAGE payload shape mismatch** — Pydantic `model_validate()` silently fails when the JSON shape doesn't match the schema. The error surfaced as an HTTP 500 with no useful detail because the generic exception handler caught it. The only way to diagnose was checking the application logs. This is why `core/exceptions.py` exists now: to wrap validation errors with structured context instead of letting them bubble as 500s.
- **LLM JSON parsing failures** — The `LLMParsingError` exception carries four fields (`raw`, `sanitized`, `finish_reason`, `parse_exception`) because I kept needing different debugging information each time. Models returning truncated responses (`finish_reason="length"`) was the hardest case because the JSON was structurally valid but semantically incomplete.
- **Frontend-side defensive check** — The fact that the frontend already had `Array.isArray()` handling for the payload means it encountered the same shape mismatch in development and added a workaround that silently diverged from what the backend actually shipped. This is a coordination failure, not a coding bug.

## Tools discovered

- **structlog** — First project using it. The processor pipeline model (add timestamps, filter levels, format output) is cleaner than standard logging. I wish I'd used it from commit one instead of adding it retrospectively.
- **ARQ** — Redis-backed async task queue. Lightweight enough to embed in a FastAPI app without Celery's complexity. The main lesson was that task queues need heartbeat monitoring and explicit retry policies, not just try/except.
- **Pydantic v2** — The `model_validate()` strictness caught several bugs (including the KNOWLEDGE_PACKAGE one) but also caused friction when models evolved. The migration from v1-style `BaseModel` patterns took some rethinking.
- **ruff** — Formatting and linting in one tool. This repo uses it. The `noqa: N818` in exception definitions suggests there was a naming convention debate I don't remember settling.

## Engineering insights

- **Partial success is the default state** — Extraction runs over 50 papers. Some will fail (rate limits, bad JSON, timeout). The pipeline runner must produce a useful result even when individual items fail. This is why `ExtractStage` returns three states (SUCCESS, PARTIAL_SUCCESS, FAILED), and `ExtractionBatchResult` separates successes from failures with structured reasons. I designed this after the first version that treated any single failure as a total failure.
- **Provider abstraction pays for itself** — The `BaseLLMProvider` interface and separate exception types (`LLMAPIError`, `LLMRateLimitError`, etc.) let the extraction service switch between OpenAI, Anthropic, or local models without changing business logic. The cost is that each new provider must translate its own SDK exceptions to these types, which is tedious but catches provider-specific behavior at the boundary.
- **Validation as a chain of small rules** — Instead of one large `validate_paper()` function, the validation module has 8 single-responsibility validators that each return zero or more `ValidationIssue` objects. This made it easy to add new rules (duplicate URL, DOI format) without touching existing logic. The scoring system (deducting points per severity) emerged from needing to rank papers numerically.
- **Graceful degradation beats crash-fast for I/O services** — The `CacheService` wraps every Redis operation in try/except and returns null values instead of raising. This contradicts typical Python advice but is correct for a cache: if Redis is down, the application should run slower, not crash. The same pattern applies to any external dependency that isn't the database.
- **LLM output normalization is a data quality layer** — Author names, institution names, dataset names all come in inconsistent forms from LLM output. The `ExtractionNormalizer` and `ExtractionValidator` classes exist to convert free text to structured, deduplicable entities. This is not glamorous work but without it the knowledge graph would be a mess of near-duplicate entries.
- **Enum serialization needs explicit string values** — `FailureReason`, `ValidationStatus`, `ArtifactStatus` — all use string enum values (`"rate_limit"`, `"valid"`, `"ready"`) rather than Python's default `auto()`. This avoids a class of bugs where renaming an enum member silently breaks serialized data in the database.

## What I would do differently next time

- **Define API contracts before implementation** — The KNOWLEDGE_PACKAGE bug would not have happened if frontend and backend had shared OpenAPI schemas as the source of truth. I'd generate clients from the spec instead of writing fetch calls manually.
- **Implement observability early** — The `logging.py` TODO is still a TODO. I'd add structlog config, request ID propagation, and span-level tracing before writing any business logic.
- **One complete vertical slice before building horizontal layers** — The empty.ts files, NotImplementedError stubs, and half-finished `logging.py` all come from building infrastructure without completing a feature. I'd ship one full feature end-to-end (investigation → retrieval → extraction → storage → display) before scaffolding anything else.
- **Don't merge stubs** — Committing code that raises `NotImplementedError` creates dead code that has to be documented, skipped in test coverage, and explained to other developers. If the interface isn't wired yet, don't merge it.
- **Write migration tests before migrations** — The JSONB `authors` column migration in commit `152a311` was added alongside the feature that needed it. I'd write a down migration and test that rollback works on a copy of production data.
- **Use `key` parameter in sort** — The `RankingEngine` sorts with a lambda instead of `functools.cmp_to_key`. Actually, the current approach is fine. I don't have a good counterexample here, which means I'm trying too hard. Stop.

## Topics I should study next

- **OpenTelemetry / tracing** — The observability module is structurally incomplete. I need distributed tracing to debug pipeline stage latencies across Redis, LLM calls, and database queries.
- **Vector databases for semantic search** — The current retrieval stack uses heuristic keyword scoring. Adding embeddings would let the copilot retrieve by meaning instead of token overlap. The `SimilarityService` stubs are waiting for this.
- **CI pipeline stabilization** — The latest commit is `stabilize CI and improve project configuration`. I keep fighting the integration pipeline. Learning GitHub Actions caching, matrix builds, and parallel test execution would save hours per iteration.
- **Database migration frameworks** — Alembic is already in use, but the `152a311` commit includes a custom JSONB migration that should have been an Alembic revision. I need to understand Alembic's autogeneration, branching, and merge resolution better.
- **Pydantic v2 type adapter** — The normalization methods in `ExtractionService` handle both dicts and pydantic models with `isinstance` checks. Pydantic's `TypeAdapter` can normalize these more cleanly, but I haven't learned it.
