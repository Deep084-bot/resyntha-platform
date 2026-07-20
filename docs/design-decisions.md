# Design Decisions

This document captures the rationale behind key architectural and design decisions in Resyntha.

---

## Deterministic Pipeline with Selective LLM Use

**Decision**: Only the Extraction and Copilot stages use LLMs. Retrieval, validation, analysis, gap detection, artifact generation, and timeline recording are fully deterministic.

**Rationale**: LLMs introduce latency, cost, and non-determinism. By restricting LLM usage to the stages that genuinely need it (knowledge extraction from papers and interactive chat), we keep the pipeline fast, cheap, and reproducible. Deterministic stages can be cached indefinitely; LLM stages have appropriate TTLs.

---

## Stage-Based Pipeline Engine

**Decision**: Generic pipeline engine with composable stages that declare consumed/produced artifact types.

**Rationale**: A stage-based architecture makes the investigation pipeline extensible, testable, and observable. Each stage is an independent unit that can be developed, tested, and deployed separately. Stage contracts (consumes/produces) enable compile-time validation of pipeline definitions. The engine supports retry, partial success, and graceful failure — critical for a system that touches external APIs.

---

## Versioned JSONB Artifacts

**Decision**: Pipeline outputs stored as versioned JSONB documents in PostgreSQL.

**Rationale**: JSONB provides schema flexibility for diverse artifact types (paper collections, knowledge packages, landscapes, gap reports) without requiring new tables for each type. Versioning enables diff comparisons and rollback. PostgreSQL indexing on JSONB path expressions supports efficient querying. This avoids the complexity of a separate document store while keeping relational data (investigations, papers, users) in normalized tables.

---

## ARQ over Celery

**Decision**: Use ARQ (Redis-backed async job queue) instead of Celery.

**Rationale**: ARQ is simpler (no broker separate from Redis, no worker monitor process), async-native (uses asyncio directly), and sufficient for our workload. Celery's additional features (task routing, complex workflows, result backends) are unnecessary for a single-queue system with straightforward pipeline execution. ARQ's keep_result and keep_result_failed settings provide built-in result retention.

---

## Manual DI over Framework Container

**Decision**: Services are wired manually via `Depends()` callables rather than a framework DI container.

**Rationale**: FastAPI's `Depends()` provides sufficient dependency injection for our needs without adding a container framework (e.g., dependency-injector). Services are created per-request with explicit dependencies (Session, Settings). This keeps the dependency graph visible in route handler signatures and avoids the indirection of a container. Worker jobs instantiate services directly, which is simpler and more testable.

---

## Module Architecture over Flat Structure

**Decision**: Domain modules follow a strict `domain/ → service/ → api/ → schemas/ → repository/` layering.

**Rationale**: The layered module architecture ensures separation of concerns. Domain models are independent of API schemas. Services orchestrate business logic without knowing about HTTP. Repositories encapsulate data access. This makes modules testable in isolation (repositories can be mocked, services tested with synthetic data) and navigable (each module is self-contained).

---

## Provider Abstraction for Retrieval and LLM

**Decision**: Retrieval providers (Semantic Scholar, arXiv, OpenAlex) and LLM providers (Groq, OpenAI) are behind abstract interfaces selected by configuration.

**Rationale**: Provider abstraction allows adding new sources without changing pipeline logic. The retrieval coordinator fetches concurrently from all configured providers, merges results, and deduplicates. The LLM abstraction allows switching providers (or using multiple) with a config change. This future-proofs the platform for new academic APIs and LLM services.

---

## Graceful Degradation

**Decision**: All external dependencies (Redis, LLM, embedding model) have fallback behavior.

**Rationale**: A platform that crashes when Redis is unavailable is not production-ready. Redis being down means caching returns None, rate limiting falls back to in-memory, and worker config returns None — but the API still responds. LLM unavailability means extraction and copilot return appropriate error messages rather than 500s. This principle extends to every external dependency.

---

## Observability-First Pipeline

**Decision**: Every pipeline stage attempt is recorded with timestamps, duration, status, and error details.

**Rationale**: Without observability, debugging pipeline failures is guesswork. The stage recorder persists the complete lifecycle of every execution: which stages ran, how long they took, whether they succeeded or failed, and any error messages. This enables detailed execution history in the UI and supports alerting on failure patterns.

---

## Hardening Over Time

**Decision**: Security, rate limiting, caching, and metrics were added incrementally rather than built in from day one.

**Rationale**: Building all production features upfront adds complexity before validating the core value proposition. The iterative approach allowed rapid prototyping of the pipeline engine and copilot, then hardening each concern independently. Each sprint focused on a single cross-cutting concern with dedicated tests and documentation.
