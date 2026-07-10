# Resyntha

[![Backend CI](https://github.com/anomalyco/resyntha/actions/workflows/backend.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/anomalyco/resyntha/actions/workflows/frontend.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/frontend.yml)
[![Quality Checks](https://github.com/anomalyco/resyntha/actions/workflows/quality.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/quality.yml)

**Research intelligence platform** — automated literature review, knowledge extraction, cross-paper analysis, and interactive AI copilot.

Resyntha turns a research topic into a structured investigation. It retrieves papers from multiple academic APIs, validates and deduplicates them, extracts structured knowledge using LLMs, computes cross-paper research landscapes, detects research gaps, and provides an interactive AI copilot grounded in the investigation's complete state. Every step runs through a configurable pipeline engine with per-stage retry, partial failure handling, and full execution history.

---

## Motivation

Existing research tools fall into two camps:

- **Conversational assistants** (ChatGPT, Perplexity) give broad answers with no investigation state, artifact persistence, or audit trail.
- **Specialized tools** (Elicit, Connected Papers, Semantic Scholar) focus on a single task and don't compose into a reproducible workflow.

Resyntha bridges this gap by treating literature review as a **reproducible pipeline**: topic → retrieval → validation → extraction → analysis → gap detection → copilot. Every intermediate result is a versioned artifact; the entire execution history is queryable.

---

## Features

| Area | Details |
|------|---------|
| **Multi-provider retrieval** | Semantic Scholar, arXiv, OpenAlex — concurrent fetching, dedup by DOI/title/URL, ranking by citations/recency/completeness |
| **Deterministic validation** | 8 rules (DuplicateDOI, DuplicateTitle, DuplicateURL, Metadata, Publication, Citation, DOIFormat, URLFormat) with composite score |
| **LLM knowledge extraction** | 11 fields per paper (research questions, findings, methodology, limitations, contributions, techniques, cited works, future work, summary) via Groq/OpenAI |
| **Cross-paper analysis** | Methodology clustering, keyword co-occurrence, technique/limitation frequency, venue/year distributions — no LLM, no hallucination risk |
| **Research gap detection** | 6 rule-based detectors (dataset, future-work, limitation, method-combination, evaluation, temporal) with severity and recommendations |
| **Interactive AI copilot** | RAG-style chat over full investigation state — intent classification, semantic retrieval, evidence aggregation, citation validation, confidence calibration |
| **Stage-based pipeline** | 8 stages (Retrieve → Validate → Persist → Extract → Analyze → Gap Detection → Artifact → Timeline) with retry, partial success, and full observability |
| **Background worker** | ARQ/Redis async queue — pipeline runs asynchronously, progress trackable via execution endpoints |
| **Versioned artifacts** | All pipeline outputs stored as versioned JSONB (PAPER_COLLECTION, VALIDATED_COLLECTION, KNOWLEDGE_PACKAGE, RESEARCH_LANDSCAPE, RESEARCH_GAP_REPORT) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│  Vite + TanStack Query + Zustand + React Router + React Flow│
└──────────────────────────┬──────────────────────────────────┘
                           │ REST (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │Health API│ │Domain    │ │Cache     │ │Rate Limit     │  │
│  │/live     │ │Modules   │ │Service   │ │Middleware     │  │
│  │/ready    │ │15 modules│ │Redis     │ │Sliding Window │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │Metrics   │ │Security  │ │Pipeline  │ │Middleware     │  │
│  │Prometheus│ │Headers   │ │Engine    │ │7 layers       │  │
│  │format    │ │CSP       │ │8 stages  │ │ordered stack  │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└─────────────┬──────────────────────────────────┬─────────────┘
              │                                  │
              ▼                                  ▼
┌─────────────────────┐          ┌──────────────────────────┐
│    PostgreSQL       │          │    Redis                 │
│  JSONB + SQLAlchemy │          │  Cache + Queue (ARQ)     │
│  Alembic migrations │          │  Rate Limit Backend      │
└─────────────────────┘          └──────────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────┐
                    │      ARQ Worker              │
                    │  Pipeline execution engine   │
                    │  Retrieval job orchestrator  │
                    └──────────────────────────────┘

External:
┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Semantic     │  │  arXiv   │  │ OpenAlex │  │  Groq    │
│ Scholar API  │  │   API    │  │   API    │  │   API    │
└──────────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Pipeline Flow

```
Research Topic
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Retrieve    │───▶│  Validate   │───▶│   Persist   │
│  3 providers │    │  8 rules    │    │  DB write   │
│  concurrent  │    │  composite  │    │  link to    │
│  + dedup     │    │  score      │    │investigation│
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Extract     │◀───│   Analyze   │◀───│ Gap Detection│
│  LLM per    │    │  clustering │    │  6 rules     │
│  paper      │    │  keywords   │    │  severity    │
│  11 fields  │    │  distros    │    │  confidence  │
└─────────────┘    └─────────────┘    └─────────────┘
      │                                        │
      ▼                                        ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Artifact   │───▶│  Timeline   │───▶│   Copilot   │
│  package    │    │  record     │    │  RAG chat   │
│  outputs    │    │  event      │    │  citations  │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Intelligence Engine (post-pipeline)

```
Extracted Knowledge
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Research   │───▶│  Landscape  │───▶│  Gap        │
│  Graph      │    │  Analyzers  │    │  Detection  │
│  normalized │    │  overview   │    │  rule-based │
│  entities   │    │  institutions│   │  report     │
│  + relations│    │  methods    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend Runtime** | Python ≥ 3.12 |
| **Web Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.x |
| **Database** | PostgreSQL 15+ (JSONB) |
| **Migrations** | Alembic |
| **Queue** | Redis + ARQ |
| **LLM** | Groq (default), OpenAI (optional) |
| **Embeddings** | sentence-transformers (local, all-MiniLM-L6-v2) |
| **Structured Logging** | structlog |
| **Validation** | Pydantic v2 |
| **Config** | pydantic-settings |
| **Frontend** | React 19, TypeScript 6, Vite 8 |
| **Styling** | Tailwind CSS 4 |
| **Server State** | TanStack Query 5, Zustand 5 |
| **Routing** | React Router 7 |
| **Graph Visualization** | React Flow |
| **Linting** | Ruff (Python), oxlint (TypeScript) |
| **CI** | GitHub Actions (3 workflows) |

---

## Project Structure

```
resyntha/
├── README.md
├── CHANGELOG.md
├── docs/                          # Cross-referenced documentation
│   ├── api.md                     # Full API reference (47 endpoints)
│   ├── architecture.md            # Pipeline and intelligence architecture
│   ├── development.md             # Development guide
│   ├── environment.md             # Environment variable reference
│   ├── production-checklist.md    # Pre-release checklist
│   └── troubleshooting.md         # Common issues and solutions
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app factory + middleware stack
│   │   ├── api/v1/                # Route aggregation
│   │   ├── bootstrap/             # Startup/shutdown/lifespan lifecycle
│   │   ├── config/                # Settings, logging, environment, constants
│   │   ├── core/                  # Middleware, context, exceptions, LLM, retrieval
│   │   ├── database/              # Engine, session, base model, health
│   │   ├── health/                # Health check routes + service
│   │   ├── infrastructure/redis/  # Redis client + health
│   │   ├── metrics/               # Prometheus-compatible metrics
│   │   ├── cache/                 # Redis cache service + decorators
│   │   ├── rate_limit/            # Rate limiting middleware + backends
│   │   ├── security/              # Security headers, CSP, upload validation
│   │   ├── observability/         # Structlog logger
│   │   ├── pipeline/              # Generic pipeline engine
│   │   ├── plugins/               # Plugin system + wrappers
│   │   ├── workers/               # ARQ worker config + jobs
│   │   ├── workflows/             # Pre-registered pipeline definitions
│   │   └── modules/               # 15 domain modules
│   ├── alembic/                   # 10 migration files
│   ├── tests/                     # 30+ test files
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   └── src/
│       ├── app/                   # App root, router, providers
│       ├── pages/                 # Route-level pages
│       ├── components/            # UI primitives + layout
│       ├── features/              # Feature-specific code
│       ├── hooks/                 # TanStack Query wrappers
│       ├── services/              # Axios API clients
│       ├── stores/                # Zustand stores
│       ├── lib/                   # Utilities
│       ├── types/                 # TypeScript interfaces
│       └── styles/                # CSS + design tokens
```

---

## Quick Start

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 22
- PostgreSQL 15+
- Redis 7+

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env — set GROQ_API_KEY, verify DATABASE_URL and REDIS_URL
alembic upgrade head
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Swagger UI at `/api/v1/docs`.

See [backend/README.md](backend/README.md) for detailed backend documentation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`. Expects backend at `http://localhost:8000/api/v1`.

### Database

```sql
CREATE DATABASE resyntha;
```

Then run `alembic upgrade head` from the backend directory.

### Redis

```bash
# macOS
brew services start redis
```

---

## Environment Variables

See [docs/environment.md](docs/environment.md) for the complete reference (60+ variables).

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | **Yes** | — | LLM provider API key |
| `SECRET_KEY` | **Yes** | — | HMAC signing (min 32 chars in production) |
| `DATABASE_URL` | No | `postgresql+psycopg://postgres:postgres@localhost:5432/resyntha` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection (empty = disabled) |
| `ENVIRONMENT` | No | `development` | `development`, `testing`, or `production` |
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Allowed origins |

---

## API Overview

See [docs/api.md](docs/api.md) for the complete reference (47 endpoints).

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | System health (DB, Redis, LLM, embeddings, worker) |
| `GET` | `/api/v1/live` | Liveness probe |
| `GET` | `/api/v1/ready` | Readiness probe |
| `GET` | `/api/v1/metrics` | Prometheus-format metrics |
| `POST` | `/api/v1/investigations` | Create investigation |
| `GET` | `/api/v1/investigations` | List investigations |
| `GET` | `/api/v1/investigations/{id}` | Get investigation |
| `DELETE` | `/api/v1/investigations/{id}` | Delete investigation |
| `GET` | `/api/v1/investigations/{id}/timeline` | Timeline |
| `POST` | `/api/v1/investigations/{id}/retrieve` | Trigger pipeline execution |
| `GET` | `/api/v1/investigations/{id}/papers` | List papers |
| `POST` | `/api/v1/investigations/{id}/executions` | Create execution |
| `GET` | `/api/v1/investigations/{id}/executions` | List executions |
| `GET` | `/api/v1/executions/{id}` | Get execution |
| `PATCH` | `/api/v1/executions/{id}` | Update execution |
| `GET` | `/api/v1/executions/{id}/stages` | List stage attempts |
| `POST` | `/api/v1/investigations/{id}/artifacts` | Create artifact |
| `GET` | `/api/v1/investigations/{id}/artifacts` | List artifacts |
| `GET` | `/api/v1/artifacts/{id}` | Get artifact |
| `PATCH` | `/api/v1/artifacts/{id}` | Update artifact |
| `GET` | `/api/v1/investigations/{id}/copilot/messages` | List copilot messages |
| `POST` | `/api/v1/investigations/{id}/copilot/chat` | Chat with copilot |
| `POST` | `/api/v1/investigations/{id}/copilot/chat/stream` | Stream chat |
| `GET` | `/api/v1/investigations/{id}/landscape` | Research landscape |
| `GET` | `/api/v1/investigations/{id}/graph` | Research graph |
| `GET` | `/api/v1/investigations/{id}/notes` | List notes |
| `POST` | `/api/v1/investigations/{id}/notes` | Create note |
| `GET` | `/api/v1/investigations/{id}/bookmarks` | List bookmarks |
| `GET` | `/api/v1/investigations/{id}/collections` | List collections |
| `GET` | `/api/v1/investigations/{id}/papers/{id}/reading-status` | Get reading status |

---

## Testing

```bash
# Backend — full suite with coverage
cd backend && python -m pytest --cov=app --cov-report=term

# Frontend
cd frontend && npx vitest run --coverage

# Linting
cd backend && ruff check .
cd frontend && npx oxlint .

# Type checking
cd backend && mypy
cd frontend && npx tsc -b
```

See [docs/development.md](docs/development.md) for the complete testing guide.

---

## CI/CD

Three GitHub Actions workflows run on push and PR:

| Workflow | Triggers | Coverage |
|----------|----------|----------|
| **Backend** | `backend/**` | Python 3.12/3.13 matrix, ruff, mypy, pytest-cov |
| **Frontend** | `frontend/**` | Node 20/22 matrix, oxlint, tsc, vitest, build |
| **Quality** | Any path | pip-audit, npm audit, gitleaks (non-blocking) |

---

## Production Readiness

See [docs/production-checklist.md](docs/production-checklist.md) for the complete checklist.

Key items before production:
- Set `ENVIRONMENT=production` — enforces PostgreSQL, blocks wildcard CORS, enables security defaults
- Generate a strong `SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Set `REDIS_URL` — production requires Redis for rate limiting + caching
- Configure `TRUSTED_HOSTS` and `CORS_ORIGINS` for your domain
- Run all tests, lint, type check, and security scans
- Verify health endpoints (`/health`, `/live`, `/ready`)
- Verify metrics endpoint (`/metrics`)
- Run database migrations (`alembic upgrade head`)

---

## Design Principles

- **Deterministic whenever possible** — Only extraction and copilot use LLMs. Ranking, validation, analysis, and gap detection are deterministic.
- **Modular architecture** — Every domain is a self-contained module with domain/service/api/schemas/repository layers.
- **Observable pipeline** — Every stage attempt is recorded with timestamps, duration, status, and errors.
- **Provider independence** — LLM and retrieval providers are selected through configuration via factory abstractions.
- **Explicit stage contracts** — Pipeline stages declare consumed/produced artifacts; validated before execution.
- **Graceful degradation** — Redis unavailable? Cache returns None, rate limit falls back to memory, worker returns None config.

---

## Contributing

See [docs/development.md](docs/development.md) for the complete guide.

1. Fork and clone
2. Follow the quick start guide
3. Create a feature branch: `git checkout -b feat/my-feature`
4. Run linting and tests
5. Open a pull request

### Conventions

- **Python**: Ruff defaults (E, F, I, N, W, UP), line length 100, double quotes
- **TypeScript**: Strict mode, ES2023 target
- **Backend modules**: `domain/ → service/ → api/ → schemas/ → repository/`
- **Pipeline stages**: Extend `PipelineStage`, declare `consumes`/`produces`
- **No commented-out code. No untracked `.env` files.**

---

## License

All rights reserved until a formal open-source license is chosen. See [LICENSE](LICENSE) (placeholder).
