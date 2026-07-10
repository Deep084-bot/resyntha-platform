# Changelog

## v0.1.0 — Initial Release (Sprint F1.10)

### Sprint D0–D6 — Foundation
- Initial project scaffolding (FastAPI + React + Vite)
- PostgreSQL schema with Alembic migrations (10 migration files)
- Investigation CRUD with timeline/status machine
- Paper retrieval from Semantic Scholar, arXiv, OpenAlex
- Concurrent provider coordinator with dedup and ranking
- 8-rule deterministic paper validation
- LLM-powered knowledge extraction (Groq, 11 fields)
- Cross-paper analysis engine (clustering, keyword extraction, distributions)
- 6-rule research gap detection
- Versioned JSONB artifact system (PAPER_COLLECTION, VALIDATED_COLLECTION, KNOWLEDGE_PACKAGE, RESEARCH_LANDSCAPE, RESEARCH_GAP_REPORT)
- Generic stage-based pipeline engine with retry and partial success
- ARQ background worker for async pipeline execution
- Interactive AI copilot with RAG context
- Investigation workspace frontend (React 19, TanStack Query, Zustand)
- Graph visualization using React Flow
- Notes, bookmarks, collections, reading status features

### Sprint F1.1 — Production Configuration
- `Settings` singleton via pydantic-settings (`lru_cache`)
- `Environment` enum with per-environment validation
- `validate_settings()` — blocks invalid combos in production
- Bootstrap lifecycle (`startup.py` / `shutdown.py` / `lifespan.py`)
- Config-driven structured logging (structlog)
- `.env` templates for all environments
- 42 configuration tests

### Sprint F1.2 — Health Checks
- `/health`, `/live`, `/ready`, `/metrics/info` endpoints
- Component checks (DB, Redis, LLM, embeddings, worker)
- Startup-time recording with build/git metadata
- 17 health tests

### Sprint F1.3 — Structured Logging & Request Tracing
- `RequestContext` / `WorkerContext` via `contextvars`
- `RequestIDMiddleware` — UUIDv4 + `X-Request-ID` header propagation
- `RequestLoggingMiddleware` — single log per request with duration
- 20 middleware tests

### Sprint F1.4 — Intelligent Caching
- `CacheService` — Redis JSON cache with graceful degradation
- Centralized key functions in `app/cache/keys.py`
- `@cached` / `@invalidate` / `@invalidate_investigation` decorators
- Cache invalidation on pipeline completion
- 37 cache tests

### Sprint F1.5 — Rate Limiting
- `RedisBackend` with sliding window (INCR+EXPIRE) + `InMemoryBackend` fallback
- `RateLimitMiddleware` with per-endpoint overrides
- `@rate_limit(method, path, ...)` decorator with global registry
- `X-RateLimit-*` + `Retry-After` headers, 429 JSON body
- 22 rate-limit tests

### Sprint F1.6 — Metrics & Observability
- Prometheus-compatible Counter, Gauge, Histogram
- `MetricsMiddleware` — active gauge, latency histogram, request counter
- `GET /api/v1/metrics` endpoint
- Metric hooks in CopilotService, InvestigationService, retrieval_job
- 25 metrics tests (1 skipped for PostgreSQL)

### Sprint F1.7 — Security Hardening
- `SecurityHeadersMiddleware` — default security headers + CSP
- `RequestSizeLimitMiddleware` — content-length + chunked body enforcement
- `TimeoutMiddleware` — asyncio.wait_for with 504 response
- Structured error handlers (422 validation, HTTPException, generic 500)
- Upload validation (MIME type, extension, size)
- CORS driven entirely from config (methods, headers, credentials)
- Security event logging (oversize, timeout, blocked origin, invalid upload)
- 34 security tests

### Sprint F1.8 — CI/CD
- GitHub Actions: `backend.yml` (Python 3.12/3.13, ruff, mypy, pytest-cov)
- GitHub Actions: `frontend.yml` (Node 20/22, oxlint, tsc, vitest, build)
- GitHub Actions: `quality.yml` (pip-audit, npm audit, gitleaks)
- Coverage artifacts and README status badges
- All backend tests pass (855+) in CI

### Sprint F1.9 — Performance & Reliability
- Connection pool tuning via config (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`)
- Pickle-to-JSON migration for `RetrievalCoordinator` cache serialization
- Async embedding offload (`SentenceTransformerProvider.embed_async` with `run_in_executor`)

### Sprint F1.10 — Documentation & Production Readiness
- Root README rewrite with Mermaid architecture diagrams
- Backend README (modules, DI, middleware, lifecycle)
- Frontend README (routing, React Query, feature folders)
- API documentation (47 endpoints)
- Environment variable reference (all fields)
- Architecture documentation (retrieval, copilot, intelligence pipelines)
- Development guide (branching, testing, modules, routes)
- Troubleshooting guide (common issues)
- Production checklist
- CHANGELOG
- docs/ directory with cross-referenced documents

## Major Milestones

| Milestone | Date | Description |
|-----------|------|-------------|
| v0.1.0 | — | Initial release with full pipeline and documentation |

## Version History

| Version | Description |
|---------|-------------|
| 0.1.0   | Initial release |
