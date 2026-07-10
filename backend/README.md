# Backend — Resyntha

FastAPI backend for the Resyntha research intelligence platform. Python ≥ 3.12.

> See [README.md](../README.md) for the project overview and quick start. See [docs/](../docs/) for in-depth reference.

---

## Folder Layout

```
app/
├── main.py                    # FastAPI app factory + middleware stack + exception handlers
├── api/v1/                    # Route aggregation (all module routers combined)
├── bootstrap/                 # Lifespan context manager (startup/shutdown)
├── config/                    # pydantic-settings singleton, environment, validation, constants
├── core/                      # Context vars, middleware, exception handlers, LLM+retrieval base
│   ├── middleware/             # 4 custom middleware classes
│   ├── llm/                   # LLM provider abstraction (Groq, OpenAI)
│   └── retrieval/             # Retrieval provider abstraction (Semantic Scholar, arXiv, OpenAlex)
├── database/                  # SQLAlchemy engine (with pool config), session, health, model registry
├── health/                    # Health check routes + service (5 endpoints)
├── infrastructure/redis/      # Redis client wrapper + health check
├── metrics/                   # Prometheus-compatible Counter/Gauge/Histogram + middleware
├── cache/                     # Redis cache service + keys + decorators (@cached, @invalidate)
├── rate_limit/                # Rate limiting middleware + Redis/InMemory backends + @rate_limit decorator
├── security/                  # Security headers middleware, CSP config, upload validation
├── observability/             # Structlog logger with context injection
├── pipeline/                  # Generic stage-based pipeline engine
│   ├── stage.py               # Abstract PipelineStage
│   ├── definition.py          # Pipeline container + contract validation
│   ├── runner.py              # Sequential stage executor with retry
│   ├── context.py             # Per-run PipelineContext
│   ├── recorder.py            # Stage lifecycle protocol
│   ├── result.py              # PipelineResult enum
│   └── stages/                # 9 concrete pipeline stages
├── plugins/                   # Plugin system — registry + per-stage wrappers
├── workers/                   # ARQ worker config + retrieval job
├── workflows/                 # Pre-registered pipeline definitions
└── modules/                   # 15 domain modules
    ├── investigation/         # Investigation CRUD, timeline, status machine
    ├── retrieval/             # Provider coordinator, merger, resolver, ranking
    ├── paper/                 # Paper + PaperSource + InvestigationPaper persistence
    ├── validation/            # 8 validators + composite scoring
    ├── extraction/            # LLM-powered knowledge extraction (11 fields)
    ├── analysis/              # Cross-paper clustering + keyword extraction + statistics
    ├── gap_detection/         # 6 rule-based gap detectors
    ├── intelligence/          # Research Graph, landscape analyzers, presentation
    ├── execution/             # Execution lifecycle + stage recording
    ├── artifact/              # Versioned JSONB artifact CRUD
    ├── copilot/               # RAG chat service, embeddings, retrieval, quality
    ├── notes/                 # Notes CRUD with source references
    ├── bookmark/              # Paper bookmark CRUD
    ├── collection/            # Paper collection CRUD
    └── reading_status/        # Paper reading status tracking
```

Each domain module follows the same internal structure:

```
modules/<name>/
├── domain/          # SQLAlchemy ORM models, enums, value objects
├── service/         # Business logic, orchestrators
├── api/             # FastAPI route definitions
├── schemas/         # Pydantic request/response models
└── repository/      # SQLAlchemy data access layer
```

---

## Middleware Stack

Registered in `app/main.py::create_app()`. Execution order (outermost → innermost):

| Middleware | Source | Purpose |
|---|---|---|
| `TrustedHostMiddleware` | FastAPI (conditional) | Validates `Host` header |
| `CORSMiddleware` | FastAPI | Configurable origins, methods, headers, credentials |
| `SecurityHeadersMiddleware` | `app/security/` | Security headers + CSP |
| `RequestSizeLimitMiddleware` | `app/core/middleware/` | Max body size enforcement (413) |
| `TimeoutMiddleware` | `app/core/middleware/` | Per-request wall-clock timeout (504) |
| `RateLimitMiddleware` | `app/rate_limit/` | Sliding window rate limits (429) |
| `MetricsMiddleware` | `app/metrics/` | Active gauge, latency histogram, counter |
| `RequestIDMiddleware` | `app/core/middleware/` | UUIDv4 + X-Request-ID header |
| `RequestLoggingMiddleware` | `app/core/middleware/` | Single completion log with duration |

Exception handlers: `RequestValidationError` → 422, `StarletteHTTPException` → JSON, `Exception` → 500 (no internal detail).

---

## Dependency Injection

No framework DI container. Services are manually wired:

- **Route handlers** create services via `Depends()` callables that accept a `Session` and optionally the `Settings` singleton.
- **Worker jobs** instantiate services directly in the job function.
- **Settings** is a pydantic-settings singleton cached with `@lru_cache`.
- **Redis client** is initialized during `lifespan` startup and stored as a module-level reference.

---

## Lifecycle

File: `app/bootstrap/lifespan.py`

### Startup
1. `configure_logging()` — structlog config from settings
2. `record_startup_time()` — BUILD_TIME and GIT_COMMIT
3. `validate_settings()` — blocks invalid production configs
4. Initialize Redis client if `REDIS_URL` is set
5. Run `initialize_services()` for cache and rate-limit backends

### Shutdown
1. Close Redis connection
2. Dispose SQLAlchemy engine

---

## Pipeline Engine

Generic stage-based executor in `app/pipeline/`:

- `PipelineStage` — abstract base with `id`, `consumes`, `produces`, `__call__`
- `PipelineDefinition` — validates stage contracts before execution
- `PipelineRunner` — sequential executor with configurable retry
- `PipelineResult` — `SUCCESS | PARTIAL_SUCCESS | FAILED | SKIPPED | RETRY`
- `StageRecorder` — persists lifecycle events to DB

The pre-registered `"retrieval"` pipeline: Retrieve → Validate → Persist → Extract → Analyze → GapDetection → Artifact → Timeline.

---

## Workers

ARQ (Redis-backed) async worker in `app/workers/`:

- **`worker.py`** — `WorkerSettings` with Redis connection, functions list, max retries (4), poll interval
- **`retrieval_job.py`** — loads investigation, constructs pipeline context, runs pipeline, records execution

Enqueue from any async context:

```python
from app.workers import enqueue_retrieval
await enqueue_retrieval(investigation_id, query, paper_limit)
```

---

## Tests

30+ files in `backend/tests/`. Run with:

```bash
cd backend
python -m pytest --cov=app --cov-report=term
python -m pytest tests/test_security.py -v  # security suite (34 tests)
python -m pytest tests/test_config.py -v    # config suite (43 tests)
python -m pytest -k "not postgresql"        # skip DB-dependent tests
```

---

## Production

See [docs/production-checklist.md](../docs/production-checklist.md) for the full checklist. Key items:

- Set `ENVIRONMENT=production` — forces PostgreSQL, blocks wildcard CORS, enables security
- Set `REDIS_URL` — production cache + rate limiting requires Redis
- Set `SECRET_KEY` — minimum 32 characters
- Configure `TRUSTED_HOSTS` and `CORS_ORIGINS`
- Run `alembic upgrade head` before serving
- Verify `/health`, `/live`, `/ready`, `/metrics`
