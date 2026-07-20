<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/cover.png">
    <img src="assets/cover.png" alt="Resyntha" width="600">
  </picture>

  # Resyntha

  **Multi-Agent Research Intelligence Platform**

  [![Backend CI](https://github.com/anomalyco/resyntha/actions/workflows/backend.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/backend.yml)
  [![Frontend CI](https://github.com/anomalyco/resyntha/actions/workflows/frontend.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/frontend.yml)
  [![Quality Checks](https://github.com/anomalyco/resyntha/actions/workflows/quality.yml/badge.svg)](https://github.com/anomalyco/resyntha/actions/workflows/quality.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python >=3.12](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
  [![Node >=22](https://img.shields.io/badge/node-22%2B-green)](https://nodejs.org/)
  [![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

  <p align="center">
    <strong>
      Automated literature review · Knowledge extraction · Cross-paper analysis · Interactive AI copilot
    </strong>
  </p>

  <p align="center">
    <a href="#features">Features</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#quick-start">Quick Start</a> ·
    <a href="#documentation">Documentation</a> ·
    <a href="#roadmap">Roadmap</a> ·
    <a href="#contributing">Contributing</a>
  </p>
</div>

---

## Elevator Pitch

**Research today is drowning in papers.** Conversational AI gives broad answers with no audit trail. Specialized tools focus on single tasks and don't compose. Resyntha bridges this gap by treating literature review as a **reproducible pipeline**: topic → retrieval → validation → extraction → analysis → gap detection → copilot. Every intermediate result is a versioned artifact; the entire execution history is queryable.

---

## Features

<table>
  <tr>
    <td width="50%">
      <h3> Multi-Provider Retrieval</h3>
      <p>Concurrent fetching from Semantic Scholar, arXiv, and OpenAlex with automatic deduplication by DOI, title, and URL. Ranking by citations, recency, and completeness.</p>
    </td>
    <td width="50%">
      <h3> Deterministic Validation</h3>
      <p>Eight composable validation rules (DuplicateDOI, DuplicateTitle, Metadata, Publication, Citation, and more) with composite scoring. No LLM hallucinations — purely deterministic.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3> LLM Knowledge Extraction</h3>
      <p>Extract 11 structured fields per paper — research questions, findings, methodology, limitations, contributions — via Groq or OpenAI. Configurable model and temperature.</p>
    </td>
    <td width="50%">
      <h3> Cross-Paper Analysis</h3>
      <p>Methodology clustering, keyword co-occurrence, technique/limitation frequency, venue/year distributions. Completely deterministic — no LLM, no hallucination risk.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3> Research Gap Detection</h3>
      <p>Six rule-based detectors — dataset, future-work, limitation, method-combination, evaluation, temporal — with severity levels and actionable recommendations.</p>
    </td>
    <td width="50%">
      <h3> Interactive AI Copilot</h3>
      <p>RAG-style chat grounded exclusively in the investigation's artifacts. Intent classification, semantic retrieval, evidence aggregation, citation validation, and confidence calibration. Streaming responses.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3> Stage-Based Pipeline Engine</h3>
      <p>Eight pipeline stages with retry, partial success, and full observability. Every stage attempt is recorded with timestamps, duration, and error details.</p>
    </td>
    <td width="50%">
      <h3> Background Workers</h3>
      <p>ARQ/Redis async queue runs pipeline executions asynchronously. Progress trackable via execution endpoints. Graceful degradation when Redis is unavailable.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3> Versioned Artifacts</h3>
      <p>All pipeline outputs stored as versioned JSONB documents (PaperCollection, KnowledgePackage, ResearchLandscape, GapReport). Enables diff comparisons and rollback.</p>
    </td>
    <td width="50%">
      <h3> Docker Deployable</h3>
      <p>Multi-stage Dockerfiles, docker-compose with health checks, nginx SPA proxy with API routing. One command to start the full stack.</p>
    </td>
  </tr>
</table>

---

## Architecture

### System Overview

```
                    ┌──────────────────────────────────────┐
                    │         React Frontend                │
                    │  Vite + TanStack Query + React Flow   │
                    │  Zustand + React Router + Tailwind    │
                    └──────────────┬───────────────────────┘
                                   │ REST API (Axios)
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │ Health   │ │ Domain   │ │ Cache    │ │ Middleware Stack    │  │
│  │ /live    │ │ Modules  │ │ Service  │ │ 9 layers (outer→   │  │
│  │ /ready   │ │ 15 mods  │ │ Redis    │ │ innermost)         │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │ Metrics  │ │ Security │ │ Pipeline │ │ Exception Handlers │  │
│  │ Prometh. │ │ Headers  │ │ Engine   │ │ 422/HTTPExc/500    │  │
│  │ format   │ │ CSP      │ │ 8 stages │ │                    │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘  │
└──────────────────────┬────────────────────────────┬──────────────┘
                       │                            │
                       ▼                            ▼
         ┌───────────────────────┐   ┌──────────────────────────┐
         │      PostgreSQL       │   │         Redis             │
         │   JSONB + SQLAlchemy  │   │   Cache + Queue (ARQ)     │
         │   Alembic migrations  │   │   Rate Limit Backend      │
         └───────────────────────┘   └──────────────┬───────────┘
                                                     │
                                                     ▼
                                    ┌──────────────────────────────┐
                                    │      ARQ Worker              │
                                    │  Pipeline execution engine   │
                                    └──────────────────────────────┘
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

### Intelligence Engine

```
Extracted Knowledge (per paper, 11 fields)
      │
      ▼
┌──────────────────────────────────────────────────┐
│  Research Graph Builder                           │
│  Normalized entity extraction                    │
│  Nodes: Paper, Method, Dataset, Technology,       │
│         Institution, Keyword, Limitation          │
│  Edges: USES_METHOD, CITES, HAS_KEYWORD, etc.    │
└──────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────┐
│  Composable Analyzers                             │
│  Overview · Institutions · Methodologies          │
│  Technologies · Datasets · Temporal · Collaborations│
└──────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────┐
│  Presentation Renderers                           │
│  JSON · Markdown · Graph (React Flow)             │
└──────────────────────────────────────────────────┘
```

### Investigation Lifecycle

```
Create Investigation ──▶ Set Topic
       │
       ▼
Trigger Pipeline (async)
       │
       ▼
  ┌──────────────────────┐
  │  ARQ Worker Enqueues │
  │  Job                 │
  └──────────┬───────────┘
             ▼
  ┌──────────────────────┐
  │  Execute Pipeline:   │
  │  1. Retrieve (3 APIs)│
  │  2. Validate (8 rules)│
  │  3. Persist (DB)     │
  │  4. Extract (LLM)    │
  │  5. Analyze (cluster) │
  │  6. Gap Detection    │
  │  7. Generate Artifacts│
  │  8. Record Timeline  │
  └──────────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │  View Results:       │
  │  Papers · Landscape   │
  │  Graph · Gaps        │
  │  Chat with Copilot   │
  └──────────────────────┘
```

---

## Screenshots

<!--
  Replace these placeholders with actual screenshots before public launch.

  Suggested screenshots to capture:
  1. Investigation Dashboard — list view with search and status indicators
  2. Pipeline Execution — real-time stage progress with timing
  3. Research Landscape — methodology clusters and keyword clouds
  4. Research Graph — interactive node/edge visualization via React Flow
  5. AI Copilot — chat interface with citations and confidence scores
  6. Gap Report — structured research gaps with severity and recommendations
-->

<table>
  <tr>
    <td align="center" width="50%">
      <strong>Investigation Dashboard</strong><br>
      <img src="assets/screenshots/dashboard.png" alt="Dashboard" width="400"><br>
      <em>Placeholder — add screenshot</em>
    </td>
    <td align="center" width="50%">
      <strong>AI Copilot Interface</strong><br>
      <img src="assets/screenshots/copilot.png" alt="Copilot" width="400"><br>
      <em>Placeholder — add screenshot</em>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <strong>Research Knowledge Graph</strong><br>
      <img src="assets/screenshots/graph.png" alt="Graph" width="400"><br>
      <em>Placeholder — add screenshot</em>
    </td>
    <td align="center" width="50%">
      <strong>Research Landscape</strong><br>
      <img src="assets/screenshots/landscape.png" alt="Landscape" width="400"><br>
      <em>Placeholder — add screenshot</em>
    </td>
  </tr>
</table>

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Runtime** | Python >= 3.12 |
| **Web Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.x |
| **Database** | PostgreSQL 15+ with JSONB |
| **Migrations** | Alembic |
| **Queue** | Redis + ARQ |
| **LLM** | Groq (default), OpenAI (optional) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Search** | pgvector (cosine similarity) |
| **Logging** | structlog |
| **Validation** | Pydantic v2 |
| **Config** | pydantic-settings |
| **Frontend** | React 19, TypeScript 6, Vite 8 |
| **Styling** | Tailwind CSS 4 |
| **Server State** | TanStack Query 5, Zustand 5 |
| **Routing** | React Router 7 |
| **Graph Viz** | React Flow 12 |
| **UI Primitives** | Radix UI, Lucide Icons |
| **Python Linting** | Ruff |
| **TS Linting** | oxlint |
| **CI** | GitHub Actions (3 workflows) |
| **Deployment** | Docker Compose |

---

## Quick Start

### Prerequisites

- Python >= 3.12
- Node.js >= 22
- Docker & Docker Compose (recommended)

### Docker (Recommended — Everything in One Command)

```bash
git clone https://github.com/anomalyco/resyntha.git
cd resyntha

# Start all services
docker compose up --build

# Open http://localhost
```

### Local Setup

<details>
<summary>Click to expand</summary>

#### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env — set GROQ_API_KEY, review DATABASE_URL and REDIS_URL
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Database

```sql
CREATE DATABASE resyntha;
```

Then: `alembic upgrade head` from the backend directory.

#### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | Yes | — | LLM provider API key |
| `SECRET_KEY` | Yes | — | HMAC signing (min 32 chars in production) |
| `DATABASE_URL` | No | `postgresql+psycopg://postgres:postgres@localhost:5432/resyntha` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection (empty = disabled) |
| `ENVIRONMENT` | No | `development` | `development`, `testing`, or `production` |

See [docs/environment.md](docs/environment.md) for the complete reference (60+ variables).
</details>

---

## Documentation

| Document | Contents |
|----------|----------|
| [Setup Guide](docs/setup.md) | Local and Docker environment setup |
| [Architecture](docs/architecture.md) | Pipeline engine, copilot, intelligence, modules |
| [API Reference](docs/api.md) | Full endpoint documentation (47 endpoints) |
| [Development Guide](docs/development.md) | Commit conventions, adding modules, testing |
| [Environment Reference](docs/environment.md) | All 60+ configuration variables |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Production Checklist](docs/production-checklist.md) | Pre-deployment verification |
| [Docker Deployment](docs/deployment/docker.md) | Docker Compose setup and commands |
| [Design Decisions](docs/design-decisions.md) | Rationale behind architectural choices |

---

## Example Investigation

```bash
# Create an investigation
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d '{"title": "LLM Agents for Code Generation", "topic": "Large language model agents for automated code generation", "paper_limit": 15}'

# Trigger pipeline execution
curl -X POST http://localhost:8000/api/v1/investigations/{id}/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "LLM agents code generation"}'

# Check pipeline status
curl http://localhost:8000/api/v1/executions/{execution_id}

# View results
curl http://localhost:8000/api/v1/investigations/{id}/papers
curl http://localhost:8000/api/v1/investigations/{id}/landscape
curl http://localhost:8000/api/v1/investigations/{id}/graph

# Chat with the copilot
curl -X POST http://localhost:8000/api/v1/investigations/{id}/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What methodologies are most commonly used in this research area?"}'
```

---

## Testing

```bash
# Backend — full suite with coverage
cd backend && python -m pytest --cov=app --cov-report=term

# Frontend
cd frontend && npx vitest run --coverage

# Linting
cd backend && ruff check . && ruff format --check .
cd frontend && npx oxlint .

# Type checking
cd backend && mypy app/
cd frontend && npx tsc -b
```

---

## Roadmap

| Version | Focus | Status |
|---------|-------|--------|
| v0.1.0 | Core pipeline engine, copilot, investigation workspace | Released |
| v0.2.0 | Docker deployment, open-source readiness | In Progress |
| v0.3.0 | Visualization, institution intelligence, reports | Planned |
| v0.4.0 | Collaboration, custom pipelines, integrations | Planned |
| v0.5.0 | Scale, multi-tenant, enterprise features | Planned |

See [docs/roadmap.md](docs/roadmap.md) for the full roadmap.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

Quick start:

1. Fork and clone
2. Follow the [setup guide](docs/setup.md)
3. Create a feature branch: `git checkout -b feat/my-feature`
4. Run linting and tests
5. Open a pull request

### Code Standards

- **Python**: Ruff defaults, line length 100, double quotes
- **TypeScript**: Strict mode, ES2023 target
- **Backend modules**: `domain/ → service/ → api/ → schemas/ → repository/`
- **Pipeline stages**: Extend `PipelineStage`, declare `consumes`/`produces`
- **No commented-out code. No untracked `.env` files.**

---

## License

Resyntha is released under the [MIT License](LICENSE). Copyright (c) 2026 anomalyco.

---

## Showcase

> **Looking for screenshots and animated demos?**  
> See the [assets/screenshots/](assets/screenshots/) directory for placeholder images.
> Before the public launch, replace these with actual screenshots and GIFs of:
>
> - Investigation creation and pipeline execution
> - Research landscape and knowledge graph visualizations
> - AI copilot chat with streaming responses
> - Gap detection reports
> - Institution intelligence reports
>
> **Contributions welcome!** If you have created visual assets or examples, please submit a PR.

---

<div align="center">
  <sub>
    Built with ❤️ by <a href="https://github.com/anomalyco">anomalyco</a>
    ·
    <a href="https://github.com/anomalyco/resyntha/issues">Report Bug</a>
    ·
    <a href="https://github.com/anomalyco/resyntha/discussions">Request Feature</a>
  </sub>
</div>
