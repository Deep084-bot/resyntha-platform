# Architecture

Resyntha's architecture centers on a **stage-based pipeline engine** that transforms a research topic into structured intelligence through sequential, observable stages.

---

## Retrieval Pipeline

The retrieval pipeline is the core workflow. It runs asynchronously via an ARQ background worker.

```
Research Topic
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│                        PIPELINE                               │
│                                                              │
│  RETRIEVE ──▶ VALIDATE ──▶ PERSIST ──▶ EXTRACT ──▶ ANALYZE   │
│   3 APIs       8 rules      DB write    LLM/copy   clusters  │
│   concurrent   composite    link to     retry      keywords  │
│   dedup        score        invest.     11 fields  distros  │
│                                                              │
│  GAP DETECTION ──▶ ARTIFACT ──▶ TIMELINE ──▶ COPILOT        │
│  6 rules         package       record       RAG chat         │
│  severity        version       event        citations        │
│  confidence      JSONB                      streaming        │
└──────────────────────────────────────────────────────────────┘
```

### Stage Details

| Stage | Input | Output | Deterministic? |
|---|---|---|---|
| **Retrieve** | investigation topic + paper limit | Paper IDs | Yes |
| **Validate** | Paper IDs | Validated papers with scores | Yes |
| **Persist** | Validated papers | DB rows (papers + investigation_papers) | Yes |
| **Extract** | Persisted papers | ExtractedKnowledge + KNOWLEDGE_PACKAGE artifact | **No** (LLM) |
| **Analyze** | ExtractedKnowledge | RESEARCH_LANDSCAPE artifact | Yes |
| **Gap Detection** | ExtractedKnowledge | RESEARCH_GAP_REPORT artifact | Yes |
| **Artifact** | Pipeline context | PAPER_COLLECTION + VALIDATED_COLLECTION artifacts | Yes |
| **Timeline** | Pipeline result | InvestigationTimeline event | Yes |

Only **Extract** and **Copilot** use LLMs. Everything else is deterministic.

### Intelligence Stage (Optional)

An additional `IntelligenceStage` builds a normalized research graph and runs composable analyzers:

- Research Graph construction (nodes: papers, methods, datasets, technologies, institutions, keywords; edges: uses, cites, relates)
- Overview analyzer
- Institution analyzer
- Methodology analyzer
- Technology analyzer
- Dataset analyzer
- Temporal analyzer
- Collaboration analyzer

---

## Copilot Pipeline

The copilot provides a RAG-style chat interface grounded in the full investigation state.

```
User Question
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  1. Intent Classification                                     │
│     QuestionIntent enum: PAPER_SUMMARY, PAPER_COMPARISON,     │
│     METHODOLOGY_COMPARISON, TREND_ANALYSIS, EVIDENCE_LOOKUP…  │
│     Each intent maps to a retrieval strategy (top_k,          │
│     priority labels/sources, hybrid scoring weights).         │
│                                                              │
│  2. Semantic Retrieval                                        │
│     a. Embed question → sentence-transformer (384-dim)       │
│     b. Vector search → pgvector (cosine distance)            │
│     c. Hybrid score → vector similarity + keyword boost       │
│     d. Context compression → deduplicate overlapping chunks   │
│     e. Budget selection → fit within MAX_CONTEXT_CHARS        │
│                                                              │
│  3. Evidence Aggregation                                      │
│     Group evidence from retrieved sections by claim/category  │
│                                                              │
│  4. Prompt Building                                           │
│     System prompt: investigation context + retrieved sections │
│     + evidence bundle + conversation history                  │
│     User prompt: question                                     │
│                                                              │
│  5. LLM Generation (Groq / OpenAI)                            │
│     Structured response with answer, citations, confidence,   │
│     reasoning. Supports streaming via async generator.        │
│                                                              │
│  6. Citation Validation                                       │
│     Verify each citation appears in retrieved context.        │
│     Discard hallucinated citations. Track keep/discard rate.  │
│                                                              │
│  7. Confidence Calibration                                    │
│     Adjust confidence score based on retrieval quality,       │
│     citation validity, evidence completeness.                 │
│                                                              │
│  8. Follow-up Generation                                      │
│     Suggest related questions based on investigation gaps.    │
└──────────────────────────────────────────────────────────────┘
```

### Retrieval Fallback

If semantic retrieval returns no sections, the copilot falls back to a **heuristic retriever** that scans investigation artifacts and extracted knowledge using keyword matching.

---

## Intelligence Pipeline

The intelligence engine transforms extracted knowledge into structured intelligence.

```
Extracted Knowledge (per paper, 11 fields)
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Research Graph Builder                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Normalized entity extraction from extracted knowledge    │ │
│  │ Node types: Paper, Method, Dataset, Technology,          │ │
│  │             Institution, Keyword, Limitation             │ │
│  │ Edge types: USES_METHOD, USES_DATASET, USES_TECHNOLOGY, │ │
│  │             HAS_KEYWORD, HAS_LIMITATION, CITES, RELATES  │ │
│  │ Deduplication by normalized label + type                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Composable Analyzers                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Overview    │ │ Institutions│ │ Methodologies           │ │
│  │ Summary     │ │ Paper       │ │ Clustering + ranking    │ │
│  │ stats       │ │ count/invest│ │ Frequency distribution  │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Technologies│ │ Datasets    │ │ Temporal                │ │
│  │ Frequency   │ │ Frequency   │ │ Publications over time  │ │
│  │ breakdown   │ │ breakdown   │ │ Year-by-year counts     │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Collaborations                                         │ │
│  │ Cross-institution paper counts                          │ │
│  │ Co-authorship network data                              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Presentation Renderers                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ JSON renderer → raw graph + analyzer output              │ │
│  │ Markdown renderer → formatted landscape report           │ │
│  │ Graph renderer → nodes + edges for React Flow            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Module Architecture

Every domain follows the same internal structure. Modules depend on each other through public service interfaces only.

```
investigation/
├── domain/          # SQLAlchemy ORM models + enums (e.g., Investigation, InvestigationStatus)
├── service/         # Business logic orchestrators (e.g., InvestigationService)
├── api/             # FastAPI routers with Depends() injection
├── schemas/         # Pydantic request/response models
└── repository/      # SQLAlchemy data access (e.g., InvestigationRepository)
```

### Module Dependency Graph

```
investigation ──▶ retrieval ──▶ paper ──▶ validation
                      │                    │
                      │                    ▼
                      │               extraction
                      │                    │
                      │                    ▼
                      │               analysis ──▶ gap_detection
                      │                    │
                      │                    ▼
                      │               execution
                      │                    │
                      │                    ▼
                      │               artifact
                      │
                      └───────────▶ copilot
                                      │
                        notes ◀───────┤
                        bookmark ◀────┤
                        collection ◀──┤
                        reading_status │
```

---

## Middleware Stack

Execution order (outermost → innermost):

```
Request
  │
  ▼
TrustedHostMiddleware  ─── validates Host header
  │
  ▼
CORSMiddleware ─── CORS headers based on config
  │
  ▼
SecurityHeadersMiddleware ─── security headers + CSP
  │
  ▼
RequestSizeLimitMiddleware ─── body size enforcement (413)
  │
  ▼
TimeoutMiddleware ─── wall-clock timeout (504)
  │
  ▼
RateLimitMiddleware ─── sliding window rate limit (429)
  │
  ▼
MetricsMiddleware ─── active gauge, latency, counter
  │
  ▼
RequestIDMiddleware ─── UUIDv4 + X-Request-ID
  │
  ▼
RequestLoggingMiddleware ─── single completion log
  │
  ▼
Handler (route)
```

Exception handlers catch errors from any middleware or route:
- `RequestValidationError` → 422 with field-level errors
- `StarletteHTTPException` → structured JSON error
- `Exception` → 500 (no internal detail exposed)

---

## Worker Architecture

```
API Server                    ARQ Worker
    │                             │
    │  POST /retrieve             │
    │  ──────────────────────►    │
    │  enqueue job                │
    │  return 202 + execution_id  │
    │                             │
    │                    ┌────────┴────────┐
    │                    │  Poll Redis     │
    │                    │  for jobs       │
    │                    └────────┬────────┘
    │                             │
    │                    ┌────────┴────────┐
    │                    │  Load           │
    │                    │  investigation  │
    │                    │  from DB        │
    │                    └────────┬────────┘
    │                             │
    │                    ┌────────┴────────┐
    │                    │  Run Pipeline   │
    │                    │  stages         │
    │                    │  sequentially   │
    │                    └────────┬────────┘
    │                             │
    │                    ┌────────┴────────┐
    │                    │  Record stages  │
    │                    │  Persist        │
    │                    │  artifacts      │
    │                    └────────┬────────┘
    │                             │
    │  GET /executions/{id}       │
    │  ◄────────────────────────  │
    │  get execution status       │
    │                             │
```

---

## Caching Architecture

```
CacheService (app/cache/service.py)
  │
  ├── Redis available? ─── Yes ──▶ Redis get/set with TTL
  │
  └── Redis unavailable? ── No ──▶ Log warning, return None

Decorators:
  @cached(key_fn, ttl)          ─── get-or-compute
  @invalidate(key_fn)           ─── evict by key
  @invalidate_investigation     ─── evict investigation-specific cache
```

---

## Rate Limiting Architecture

```
RateLimitMiddleware
  │
  ├── RateLimitBackend
  │     │
  │     ├── RedisBackend ─── INCR + EXPIRE (atomic sliding window)
  │     │                      key: "rate_limit:{identity}:{route}"
  │     │
  │     └── InMemoryBackend ── dict with timestamps (dev/test fallback)
  │
  ├── @rate_limit(method, path, limit, window) decorator
  │     └── Registers override in _override_registry
  │
  └── Response headers: X-RateLimit-Limit, X-RateLimit-Remaining,
                        X-RateLimit-Reset, Retry-After
```
