# Changelog

## v1.0.0 — Launch Readiness & Release Candidate (Sprint P4)

### Security
- Fixed XSS vulnerability in MarkdownViewer — sanitized `href` attributes to block `javascript:` URLs
- Added URL protocol validation for all rendered links
- Added `rel="noopener noreferrer nofollow"` to all external links
- Fixed `escapeHtml()` to escape single quotes (`'`)
- Removed `backend/.env` file containing live API credentials from version control
- Sanitized uploaded filenames with `os.path.basename()` to prevent path traversal
- Suppressed raw API error messages in copilot streaming and error boundary UI
- Removed redundant `invalidateQueries` after copilot stream success (data leak reduction)

### Infrastructure
- Multi-stage Dockerfiles with non-root users
- Docker Compose health checks and dependency ordering
- Security headers in nginx: X-Content-Type-Options, X-Frame-Options, HSTS, Referrer-Policy
- Production environment variable validation at startup
- Added per-stage pipeline timeout (360s default) to prevent hung workers
- Added `.editorconfig` for consistent formatting across editors

### Pipeline & Workflow
- Empty extraction returns SKIPPED instead of SUCCESS
- Added unique partial index on `extracted_knowledge(paper_id, execution_id)` for dedup
- Added `has_active_execution()` guard on `create_execution` route (409 Conflict)
- Added content-quality gate in extraction — rejects LLM output with empty summary
- Added delete-during-execution guard on investigation deletion (409 Conflict)
- Pipeline retry policy changed from 0 to 2 retries with exponential backoff
- Parallel LLM extraction with `asyncio.Semaphore(5)` — 5x speedup for multi-paper investigations
- Added 120-second timeout on copilot streaming endpoint

### Analysis & Intelligence
- Fixed venue distribution using `venue` field instead of `paper_title`
- Populated `year_dist` and `citation_stats` from Paper database rows
- Added missing DB indexes on `CopilotMessage.conversation_id` and `Bookmark.paper_id`

### Frontend
- Copilot stream error no longer rolls back optimistic user message
- Added `onlyRenderVisibleElements` to ReactFlow for large graph performance
- Memoized `filteredData` in GraphPage to prevent layout recomputation on unrelated state changes
- Memoized `InvestigationRunContext` value to prevent cascading re-renders during polling
- Removed raw `Error.message` rendering from error boundary UI
- Replaced raw response body with generic error message in copilot stream error handler

### Quality & Reliability
- Added global `ErrorBoundary` to prevent blank-screen crashes on uncaught React errors
- Fixed deprecated status code constants across backend and tests
- Added database connection pool cleanup on shutdown (`engine.dispose()`)
- Added per-environment SECRET_KEY validation
- Removed dead `sync_wrapper` branches from cache decorators
- Fixed `datetime.utcnow()` deprecation across all backend code
- Replaced hardcoded `POSTGRES_PASSWORD` with environment variable reference
- Fixed test health checks to LLM component availability

### Version
- All configuration files aligned to v1.0.0

## v0.2.0 — Production Engineering & Open Source Excellence (Sprint P2–P3)

### Sprint P2 — Production Engineering (Docker)
- Multi-stage Dockerfiles for backend (Python 3.12-slim) and frontend (Node 22 → nginx:alpine)
- `docker-compose.yml` with PostgreSQL 16, Redis 7, backend, ARQ worker, and frontend services
- `docker-compose.override.yml` for development hot-reload
- `backend/.env.docker` with Docker-optimized defaults
- Custom `nginx.conf` for SPA routing + `/api/` proxy
- Health checks and dependency ordering for all services
- Comprehensive deployment docs at `docs/deployment/docker.md`

### Sprint P3 — Open Source Excellence
- Complete README redesign with hero, badges, architecture, roadmap, showcase
- Community files: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md
- GitHub issue templates (bug report, feature request, question)
- Pull request template
- Filled documentation placeholders (setup.md, roadmap.md, design-decisions.md)
- Root `.gitignore` with project cleanup
- Updated CHANGELOG with all sprint entries
- Project organization audit and naming consistency check

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
| v1.0.0 | — | Launch readiness, security hardening, production infrastructure |

## Version History

| Version | Description |
|---------|-------------|
| 1.0.0   | Launch readiness — security audit, infrastructure hardening, XSS fixes, global error boundary |
| 0.2.0   | Production Engineering & Open Source Excellence — Docker, community files, documentation |
| 0.1.0   | Initial release — pipeline engine, copilot, investigation workspace, full test suite |
