# Resyntha

**AI research intelligence platform — automated literature review, knowledge extraction, cross-paper analysis, and interactive copilot.**

Resyntha turns a research topic into a structured investigation. It retrieves papers from multiple academic APIs, validates and deduplicates them, extracts structured knowledge using LLMs, computes cross-paper research landscapes, detects research gaps, and provides an interactive AI copilot that answers questions backed by your investigation's data.

Every step runs through a configurable pipeline engine with per-stage retry, partial failure handling, and full execution history.

---

## Why Resyntha?

Existing research tools fall into two camps:

- **Conversational assistants** (ChatGPT, Perplexity) give broad answers with no investigation state, no artifact persistence, and no audit trail.
- **Specialized tools** (Elicit, Connected Papers, Semantic Scholar) focus on a single task — retrieval or citation graphs — and don't compose into a reproducible workflow.

Resyntha bridges this gap by treating literature review as a **reproducible pipeline**:

1. A topic enters → papers are retrieved from multiple sources concurrently.
2. Retrieved papers are validated, deduplicated, and scored.
3. Each paper passes through an LLM that extracts structured knowledge.
4. Cross-paper analysis computes clusters, trends, and distributions — entirely deterministically, with no hallucination risk.
5. Rule-based gap detection identifies dataset gaps, temporal gaps, method combination opportunities, and more.
6. Every result is persisted as a versioned artifact with a known provenance chain.
7. An AI copilot answers natural-language questions over the complete investigation state.

The outcome is a **persistent, auditable, composable research intelligence platform** — not a single ephemeral chat response.

---

## Key Features

### Research Retrieval

| Provider | Scope |
|---|---|
| [Semantic Scholar](https://semanticscholar.org/) | Academic paper search with citation data |
| [arXiv](https://arxiv.org/) | Open-access preprint repository |
| [OpenAlex](https://openalex.org/) | Comprehensive open scholarly index |

Papers are fetched from all providers concurrently. A duplicate resolver merges matches by DOI, external identifiers, title similarity, and URL. A ranking engine scores each paper by citation count (35%), recency (25%), metadata completeness (20%), and provider confidence (20%).

### Intelligent Validation

Eight deterministic validators run on every retrieved paper:

- **DuplicateDOI** — detects papers sharing a DOI within the same investigation
- **DuplicateTitle** — fuzzy title matching
- **DuplicateURL** — URL-based deduplication
- **Metadata** — checks completeness of title, abstract, authors, year, DOI
- **Publication** — validates publication venue formatting
- **Citation** — verifies citation count presence
- **DOIFormat** — regex validation of DOI structure
- **URLFormat** — URL format check

Each validator returns PASS, WARNING, or FAIL. A composite score (0–100) and overall status (VALID / WARNING / INVALID) are computed per paper.

### LLM-Powered Knowledge Extraction

Each validated paper is sent through a Groq-hosted LLM (default: `llama-3.3-70b-versatile`) that extracts 11 structured fields:

- Research questions
- Key findings
- Methodology
- Limitations
- Key contributions
- Relevant techniques / datasets
- Cited works
- Future work
- Summary

The extraction includes automatic retries with exponential backoff, robust JSON parsing that handles code fences and explanatory text, and per-paper failure classification (rate limit, timeout, malformed JSON, validation error, API error). OpenAI is supported as an optional alternative provider.

### Cross-Paper Analysis

After extraction, a deterministic engine computes the **research landscape** — no LLM calls, no hallucination risk:

- Methodology clustering and ranking
- Keyword extraction and co-occurrence clusters
- Technique/limitation/future-work frequency distributions
- Venue and publication-year distributions
- Citation statistics

### Research Gap Detection

Six rule-based detectors identify research opportunities:

| Rule | Detects |
|---|---|
| `DatasetGap` | Papers that lack dataset references |
| `FutureWorkGap` | Papers that propose no future work |
| `LimitationGap` | Papers that omit limitations |
| `MethodCombinationGap` | Under-explored methodology pairings |
| `EvaluationGap` | Papers without evaluation metrics |
| `TemporalGap` | Stale citation patterns |

Each gap includes a severity rating, confidence score, and actionable recommendation.

### Interactive AI Copilot

After the pipeline completes, a RAG-style chat endpoint lets users ask natural-language questions about their investigation. The copilot:

1. Builds context from all papers, extracted knowledge, artifacts, and the gap report.
2. Sends the context along with the user's question to the LLM.
3. Returns a cited answer with suggested follow-up questions.
4. Persists the conversation and message history.

### Execution Engine

A generic stage-based pipeline engine drives the entire workflow:

- **`PipelineStage`** — abstract base class with declared `consumes` and `produces` artifact contracts.
- **`PipelineRunner`** — sequential stage executor with configurable retry policy (max retries, exponential backoff).
- **`StageRecorder`** — protocol for persisting stage lifecycle events (started, completed, failed, partial success).
- **`PipelineResult`** — five outcome values: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `RETRY`.

The engine is fully decoupled from domain logic — any sequence of stages can be assembled and run.

### Artifact System

All pipeline outputs are versioned artifacts stored as JSONB in PostgreSQL:

| Artifact Type | Produced By | Content |
|---|---|---|
| `PAPER_COLLECTION` | ArtifactStage | Paper metadata and identifiers |
| `VALIDATED_COLLECTION` | ArtifactStage | Validation results and scores |
| `KNOWLEDGE_PACKAGE` | ExtractStage | Per-paper structured knowledge |
| `RESEARCH_LANDSCAPE` | AnalyzeStage | Clusters, keywords, distributions |
| `RESEARCH_GAP_REPORT` | GapDetectionStage | Detected gaps with recommendations |

Additional artifact types (`COMPARISON_MATRIX`, `TREND_REPORT`, `OPPORTUNITY_REPORT`, `RESEARCH_IDEAS`, `FINAL_REPORT`) are defined in the schema but not yet implemented.

---

## Architecture

```mermaid
graph TB
    Client["React Frontend<br/>Vite + TanStack Query"]
    API["FastAPI Backend<br/>Python 3.12"]
    Worker["ARQ Worker<br/>Redis-backed"]
    DB[("PostgreSQL<br/>JSONB + SQLAlchemy")]
    Redis[("Redis<br/>Queue + Cache")]
    LLM["Groq API<br/>llama-3.3-70b"]
    ResearchAPI["Research APIs<br/>Semantic Scholar / arXiv / OpenAlex"]

    subgraph Frontend
        Client
    end

    subgraph Backend
        API
        Worker
        DB
        Redis
    end

    subgraph External
        LLM
        ResearchAPI
    end

    Client -->|REST| API
    API -->|enqueue job| Redis
    Worker -->|poll jobs| Redis
    Worker -->|read/write| DB
    Worker -->|extraction| LLM
    Worker -->|paper search| ResearchAPI
    API -->|read/write| DB
    Worker -->|record stages| DB
```

### Component Breakdown

**Frontend** — React 19 with TypeScript, Vite, Tailwind CSS 4, and TanStack Query. Dark-themed workspace with tabs for every pipeline output. Communicates with the backend via REST (Axios).

**FastAPI Backend** — Modular vertical-slice architecture. Each domain (investigation, retrieval, paper, validation, extraction, analysis, gap detection, execution, artifact, copilot) is a self-contained module with `domain/`, `service/`, `api/`, `schemas/`, and `repository/` layers.

**Pipeline Engine** — A generic framework in `app/pipeline/` that can compose any set of stages. The pre-registered "retrieval" pipeline chains 8 stages (Retrieve → Validate → Persist → Extract → Analyze → GapDetection → Artifact → Timeline). Stages declare their data contracts explicitly through `consumes` and `produces` lists; the definition validates the graph before execution.

**ARQ Worker** — Long-running pipeline jobs are enqueued to Redis and executed by an ARQ background worker. The worker loads investigation state from the database, constructs a `PipelineContext`, runs the pipeline via `PipelineDefinition`, records every stage attempt, and persists the final results.

**PostgreSQL** — Primary data store with JSONB columns for flexible payloads (artifacts, paper metadata, extraction results). Alembic handles schema migrations.

**External APIs** — Three paper providers (Semantic Scholar, arXiv, OpenAlex) for retrieval, and Groq (with optional OpenAI) for LLM inference.

---

## Pipeline Overview

```mermaid
flowchart LR
    Topic["Research Topic"] --> Retrieve

    subgraph Pipeline
        Retrieve["Retrieve<br/>3 providers<br/>concurrent"]
        Validate["Validate<br/>8 rules<br/>composite score"]
        Persist["Persist<br/>DB write<br/>investigation link"]
        Extract["Extract<br/>LLM per paper<br/>11 fields"]
        Analyze["Analyze<br/>Deterministic<br/>landscape"]
        Gaps["Gap Detection<br/>6 rules<br/>severity + confidence"]
        Artifact["Artifact<br/>package outputs"]
        Timeline["Timeline<br/>record event"]

        Retrieve --> Validate
        Validate --> Persist
        Persist --> Extract
        Extract --> Analyze
        Analyze --> Gaps
        Gaps --> Artifact
        Artifact --> Timeline
    end

    Timeline --> Copilot["Copilot<br/>RAG chat"]

    style Extract fill:#4a6fa5,color:#fff
    style Copilot fill:#4a6fa5,color:#fff
```

### Stage Details

| Stage | Input | Output | Nature |
|---|---|---|---|
| **Retrieve** | investigation topic + paper limit | `paper_ids` | Concurrent HTTP calls to 3 APIs, dedup, ranking |
| **Validate** | `paper_ids` | `validated_papers` | 8 deterministic rules, no LLM |
| **Persist** | `validated_papers` | persisted DB rows | Writes to `papers` + `investigation_papers` tables |
| **Extract** | persisted papers | `ExtractedKnowledge` rows + `KNOWLEDGE_PACKAGE` artifact | LLM per paper with retry + failure classification |
| **Analyze** | `ExtractedKnowledge` records | `RESEARCH_LANDSCAPE` artifact | Deterministic clustering and statistics |
| **Gap Detection** | `ExtractedKnowledge` records | `RESEARCH_GAP_REPORT` artifact | Deterministic rule matching |
| **Artifact** | pipeline context | `PAPER_COLLECTION` + `VALIDATED_COLLECTION` | Packaging stage outputs as artifacts |
| **Timeline** | pipeline result | `InvestigationTimeline` event | Records pipeline completion |

Two stages (Extract and Copilot) use LLMs. All other stages are deterministic.

---

## Project Structure

```
resyntha/
├── backend/
│   ├── app/
│   │   ├── api/                        # Root API v1 router
│   │   │   └── v1/                     # Route aggregation
│   │   ├── config/                     # Settings, logging, environment
│   │   │   ├── settings.py             # pydantic-settings (single source of truth)
│   │   │   └── environment.py          # Environment detection
│   │   ├── core/                       # App lifecycle, logging
│   │   ├── database/                   # SQLAlchemy engine, session, base model
│   │   ├── infrastructure/redis/       # Redis client and health check
│   │   ├── observability/              # Structured logging (structlog)
│   │   ├── pipeline/                   # Generic pipeline engine
│   │   │   ├── stages/                 # 8 concrete pipeline stages
│   │   │   ├── runner.py              # Sequential stage executor
│   │   │   ├── recorder.py            # Stage lifecycle protocol
│   │   │   ├── definition.py          # Pipeline container + validation
│   │   │   ├── context.py             # Per-run context dataclass
│   │   │   ├── result.py              # PipelineResult enum
│   │   │   ├── retry.py               # Retry policy
│   │   │   └── stage.py               # Abstract PipelineStage
│   │   ├── plugins/                    # Plugin system
│   │   │   ├── registry.py            # Named pipeline map
│   │   │   └── wrappers.py            # Plugin adapters for each stage
│   │   ├── workers/                    # ARQ background workers
│   │   │   ├── worker.py              # Worker config + enqueue
│   │   │   └── retrieval_job.py       # Main pipeline worker
│   │   └── modules/                    # Domain modules
│   │       ├── investigation/          # CRUD + timeline + status machine
│   │       ├── retrieval/             # 3 providers + coordinator + ranking
│   │       ├── paper/                 # Paper / PaperSource / InvestigationPaper
│   │       ├── validation/            # 8 validators + composite scoring
│   │       ├── extraction/            # LLM provider + service + prompts
│   │       ├── analysis/              # Clustering + statistics + landscape
│   │       ├── gap_detection/         # 6 rules + report builder
│   │       ├── execution/             # Execution + stage recording
│   │       ├── artifact/              # CRUD + status machine + response
│   │       └── copilot/               # RAG chat service
│   ├── alembic/                        # 8 migration files
│   ├── tests/                          # Test suite (single test file)
│   ├── pyproject.toml                  # Python project config
│   └── .env.example                    # Environment variable template
├── frontend/
│   └── src/
│       ├── pages/                      # 12 route pages
│       ├── components/ui/              # Design system primitives
│       ├── hooks/                      # TanStack Query wrappers
│       ├── services/                   # Axios API clients
│       ├── stores/                     # Zustand auth store
│       ├── lib/                        # Utilities (api client, formatters)
│       ├── types/                      # TypeScript interfaces + query keys
│       └── styles/                     # Tailwind globals + design tokens
└── README.md
```

Every domain module follows a consistent internal structure:

```
modules/<name>/
├── domain/          # ORM models, enums, value objects
├── service/         # Business logic, orchestrators
├── api/             # FastAPI route definitions
├── schemas/         # Pydantic request/response models
└── repository/      # SQLAlchemy data access
```

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Backend Runtime** | Python | ≥ 3.12 |
| **Web Framework** | FastAPI | latest |
| **ORM** | SQLAlchemy | 2.x |
| **Database** | PostgreSQL | 15+ (JSONB) |
| **Migrations** | Alembic | latest |
| **Queue** | Redis + ARQ | latest |
| **LLM Provider** | Groq (default), OpenAI (optional) | — |
| **Structured Logging** | structlog | latest |
| **Validation** | Pydantic v2 | — |
| **Frontend Framework** | React | 19 |
| **Build Tool** | Vite | 8 |
| **Language** | TypeScript | 6 |
| **Styling** | Tailwind CSS | 4 |
| **Server State** | TanStack Query | 5 |
| **Client State** | Zustand | 5 |
| **Routing** | React Router | 7 |
| **Icons** | Lucide React | latest |
| **UI Primitives** | Radix UI | latest |
| **Python Linting** | Ruff | latest |
| **TS Linting** | oxlint | latest |

---

## Installation

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 22
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
# Clone and enter the backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (including dev extras for testing/linting)
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
```

Edit `.env` with your local values. At minimum, set `GROQ_API_KEY` (get a free key at [console.groq.com](https://console.groq.com/)) and verify `DATABASE_URL` and `REDIS_URL`.

```bash
# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`. OpenAPI docs are at `http://localhost:8000/docs`.

### Frontend Setup

```bash
# From the repository root
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend is now available at `http://localhost:5173`. It expects the backend at `http://localhost:8000/api/v1` (configured in `src/lib/api.ts`).

### Database Setup (Quick Reference)

```sql
CREATE DATABASE resyntha;
```

Then run `alembic upgrade head` from the backend directory. The initial migration creates all tables: `investigations`, `papers`, `paper_sources`, `investigation_papers`, `executions`, `execution_stages`, `artifacts`, `investigation_timeline`, `extracted_knowledge`, `copilot_conversations`, `copilot_messages`, plus supporting type enums.

### Redis

Make sure Redis is running on the default port (`localhost:6379`). On macOS:

```bash
brew services start redis
```

---

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_NAME` | No | resyntha | Application name used in logging and OpenAPI |
| `APP_VERSION` | No | 0.1.0 | SemVer string |
| `ENVIRONMENT` | No | development | `development`, `testing`, or `production` |
| `DEBUG` | No | false | Enable debug logging and verbose error responses |
| `SECRET_KEY` | **Yes** | — | HMAC signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `DATABASE_URL` | No | postgresql+psycopg://postgres:postgres@localhost:5432/resyntha | Full PostgreSQL connection string |
| `REDIS_URL` | No | redis://localhost:6379/0 | Redis connection string |
| `GROQ_API_KEY` | **Yes** | — | Groq API key for LLM access |
| `LLM_MODEL` | No | llama-3.3-70b-versatile | Groq model identifier |
| `LLM_PROVIDER` | No | groq | LLM provider (`groq` or `openai`) |
| `LLM_MAX_TOKENS` | No | 4096 | Max tokens per LLM response |
| `LLM_TEMPERATURE` | No | 0.3 | LLM temperature |
| `OPENAI_API_KEY` | No | — | OpenAI API key (required if `LLM_PROVIDER=openai`) |
| `API_V1_PREFIX` | No | /api/v1 | REST API prefix |
| `CORS_ORIGINS` | No | localhost:5173,3000,8000 | Comma-separated allowed CORS origins |

> **NOTE:** `SECRET_KEY` and `GROQ_API_KEY` are the only mandatory values. Everything else has a working default for local development.

---

## API Overview

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check (DB + Redis) |
| `POST` | `/api/v1/investigations` | Create a research investigation |
| `GET` | `/api/v1/investigations` | List all investigations |
| `GET` | `/api/v1/investigations/{id}` | Get investigation details |
| `DELETE` | `/api/v1/investigations/{id}` | Delete an investigation |
| `GET` | `/api/v1/investigations/{id}/timeline` | Get investigation timeline |
| `POST` | `/api/v1/investigations/{id}/retrieve` | Enqueue retrieval pipeline |
| `GET` | `/api/v1/investigations/{id}/papers` | List retrieved papers |
| `GET` | `/api/v1/investigations/{id}/executions` | List pipeline executions |
| `GET` | `/api/v1/executions/{id}` | Get execution details |
| `PATCH` | `/api/v1/executions/{id}` | Update execution status |
| `GET` | `/api/v1/executions/{id}/stages` | List stage attempts |
| `GET` | `/api/v1/investigations/{id}/artifacts` | List investigation artifacts |
| `GET` | `/api/v1/artifacts/{id}` | Get single artifact |
| `PATCH` | `/api/v1/artifacts/{id}` | Update artifact status/payload |
| `POST` | `/api/v1/investigations/{id}/copilot/chat` | Send copilot message |

Interactive API documentation is automatically available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## Investigation Workflow

### 1. Create an Investigation

```bash
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d '{"title": "LLM Agents for Code Generation", "topic": "Large language model agents for automated code generation and software development", "paper_limit": 15}'
```

Returns an `investigation_id` — this is the handle for everything that follows.

### 2. Trigger Retrieval

```bash
curl -X POST http://localhost:8000/api/v1/investigations/{id}/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "LLM agents code generation", "paper_limit": 15}'
```

Returns `202 Accepted` with an `execution_id`. The pipeline runs in the background via ARQ worker.

### 3. Track Pipeline Progress

```bash
# Check execution status
curl http://localhost:8000/api/v1/executions/{execution_id}

# List per-stage results
curl http://localhost:8000/api/v1/executions/{execution_id}/stages
```

Each stage transitions through `PENDING → RUNNING → COMPLETED` (or `FAILED`). A stage may show `PARTIAL_SUCCESS` if some papers failed extraction while others succeeded — the pipeline continues.

### 4. Review Results

```bash
# Retrieved papers
curl http://localhost:8000/api/v1/investigations/{id}/papers

# All artifacts (knowledge package, landscape, gap report, etc.)
curl http://localhost:8000/api/v1/investigations/{id}/artifacts
```

Artifacts are versioned JSONB payloads. Each one has a type (`KNOWLEDGE_PACKAGE`, `RESEARCH_LANDSCAPE`, `RESEARCH_GAP_REPORT`, etc.) and a status (`PENDING`, `GENERATING`, `READY`, `FAILED`).

### 5. Chat with Copilot

```bash
curl -X POST http://localhost:8000/api/v1/investigations/{id}/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What methodologies are most commonly used in this research area?"}'
```

The copilot builds context from all papers, extractions, artifacts, and the gap report, then returns a cited answer with suggested follow-up questions.

---

## Design Principles

### Deterministic Whenever Possible

Only knowledge extraction and the copilot use LLMs. Retrieval ranking, validation, cross-paper analysis, and gap detection are all deterministic — they produce the same output for the same input every time. This makes results auditable and reproducible.

### Modular Architecture

Every domain is a self-contained module with its own data models, business logic, API endpoints, request/response schemas, and repository. Modules depend on each other through their public service interfaces, never through shared internals.

### Observable Pipeline

The pipeline runner records every stage attempt with timestamps, duration, status, and error messages. The execution history is persisted and queryable — there is no opaque processing stage.

### Provider Independence

Retrieval providers (Semantic Scholar, arXiv, OpenAlex) and LLM providers (Groq, OpenAI) are selected through configuration, not hard-coded imports. The `ProviderFactory` and `BaseLLMProvider` abstractions make it straightforward to add new providers.

### Explicit Stage Contracts

Every pipeline stage declares its required inputs (`consumes`) and produced outputs (`produces`) as string lists. The pipeline definition validates these contracts before execution, catching missing dependencies at configuration time rather than at runtime.

### Extensibility

New stages implement `PipelineStage`, declare their contracts, and register in `PipelineRegistry`. New retrieval providers implement `BaseProvider`. New LLM providers subclass `BaseLLMProvider`. New gap detection rules subclass `BaseGapRule`. The plugin architecture requires touching no existing code.

---

## Current Limitations

- **Groq rate limits** — The free Groq tier has a daily rate limit that can cause extraction failures for large paper sets. Pipeline handles this with `PARTIAL_SUCCESS` and per-paper failure classification.
- **No Docker setup** — PostgreSQL and Redis must be installed manually. A `docker-compose.yml` is planned.
- **No CI/CD** — GitHub Actions or equivalent are not yet configured.
- **Limited test coverage** — One test file (`tests/test_llm_parser.py`) exists. The project needs comprehensive unit and integration tests.
- **Screenshots pending** — Screenshots and demo GIFs have not been created yet.
- **LLM-only extraction** — The extraction module currently supports only Groq (with OpenAI as optional). Other providers (Anthropic, Ollama, local models) are not yet integrated.
- **No authentication** — The API has no user authentication layer. The `SECRET_KEY` is defined but not yet used for JWT or session signing.
- **Several artifact types unimplemented** — `COMPARISON_MATRIX`, `TREND_REPORT`, `OPPORTUNITY_REPORT`, `RESEARCH_IDEAS`, and `FINAL_REPORT` are defined in the schema but have no builders yet.
- **Single pipeline** — Only one pipeline ("retrieval") is registered. The engine supports multiple pipelines, but none are configured yet.

---

## Roadmap

### Current (v0.1.0)

- [x] Multi-provider paper retrieval (Semantic Scholar, arXiv, OpenAlex)
- [x] Paper validation with 8 rules and composite scoring
- [x] LLM-powered knowledge extraction with retry and failure classification
- [x] Deterministic cross-paper analysis (clustering, keyword extraction, distributions)
- [x] Rule-based gap detection (6 rules)
- [x] Generic stage-based pipeline engine with retry and partial success
- [x] Execution history and stage recording
- [x] Versioned artifact system with JSONB storage
- [x] Background worker via ARQ/Redis
- [x] Interactive AI copilot with RAG context
- [x] Dark-themed React workspace

### Next

- [ ] Docker Compose setup (PostgreSQL + Redis + backend + frontend)
- [ ] CI/CD pipeline (lint → test → build)
- [ ] E2E test suite
- [ ] Comparison Matrix artifact builder
- [ ] Trend Report artifact builder
- [ ] Provider abstraction for retrieval (formalize `BaseProvider` interface for all providers)
- [ ] LLM Router — route papers to optimal provider/model based on content
- [ ] Export artifacts (PDF, CSV, BibTeX)

### Future

- [ ] User authentication and multi-tenant investigations
- [ ] Ollama provider for self-hosted LLM inference
- [ ] Semantic search over artifact content
- [ ] Scheduled / recurring retrieval pipelines
- [ ] Collaborative investigation sharing
- [ ] Plugin marketplace for custom stages and rules
- [ ] WebSocket-based pipeline progress streaming

---

## Contributing

Contributions are welcome. The project is in early development, so the contribution surface is broad.

### Getting Started

1. Fork the repository.
2. Follow the [Installation](#installation) guide to set up your local environment.
3. Create a feature branch: `git checkout -b feat/my-feature`.
4. Make your changes.
5. Run linting:

   ```bash
   cd backend && ruff check .
   cd frontend && npx oxlint .
   ```

6. Run tests:

   ```bash
   cd backend && python -m pytest
   ```

7. Commit with a descriptive message and open a pull request.

### Coding Conventions

- **Python**: Follow Ruff defaults (`select = ["E", "F", "I", "N", "W", "UP"]`), line length 100, double quotes.
- **TypeScript**: Strict mode, ES2023 target, bundler module resolution.
- **Backend modules**: Follow the `domain/ → service/ → api/ → schemas/ → repository/` convention.
- **Pipeline stages**: Extend `PipelineStage`, declare `consumes`/`produces`, register in `PipelineRegistry`.
- **No commented-out code. No untracked `.env` files.**

---

## License

A license file has not yet been chosen. All rights are reserved until a formal open-source license is added. This will be resolved in an upcoming release.

---

## Acknowledgements

Resyntha would not exist without the infrastructure and data provided by:

- [Semantic Scholar API](https://api.semanticscholar.org/) — academic paper search and citation data
- [arXiv API](https://info.arxiv.org/help/api/index.html) — open-access preprint repository
- [OpenAlex API](https://openalex.org/) — comprehensive open scholarly index
- [Groq](https://groq.com/) — fast LLM inference (default provider)
- [FastAPI](https://fastapi.tiangolo.com/) — high-performance Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python ORM and toolkit
- [Alembic](https://alembic.sqlalchemy.org/) — lightweight database migrations
- [Pydantic](https://docs.pydantic.dev/) — data validation and settings management
- [structlog](https://www.structlog.org/) — structured logging for Python
- [React](https://react.dev/) — UI framework
- [TanStack Query](https://tanstack.com/query) — server state management
- [Tailwind CSS](https://tailwindcss.com/) — utility-first CSS framework
- [Radix UI](https://www.radix-ui.com/) — accessible UI primitives
- [Lucide](https://lucide.dev/) — open-source icon library
