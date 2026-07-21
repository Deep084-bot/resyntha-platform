# Environment Variables Reference

All configuration flows through a single pydantic-settings `Settings` singleton (`backend/app/config/settings.py`). Variables are loaded from `.env` files (`.env.development`, `.env.testing`, `.env.production`).

---

## Application

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `APP_NAME` | `str` | `resyntha` | No | Keep default |
| `APP_VERSION` | `str` | `1.0.0` | No | Match release tag |
| `ENVIRONMENT` | `enum` | `development` | No | Set to `production` |
| `DEBUG` | `bool` | `false` | No | `false` |

`ENVIRONMENT` values: `development`, `testing`, `production`. In production:
- `DATABASE_URL` must use PostgreSQL (not SQLite)
- `SECRET_KEY` min 32 characters enforced
- Wildcard CORS origins (`*`) rejected
- Maximum body/timeout size > 0 enforced

---

## Database

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `DATABASE_URL` | `str` | `postgresql+psycopg://postgres:postgres@localhost:5432/resyntha` | No | Set to production PostgreSQL with SSL |
| `DB_POOL_SIZE` | `int` | `10` | No | 20–50 depending on connection load |
| `DB_MAX_OVERFLOW` | `int` | `20` | No | 2× pool size |
| `DB_POOL_TIMEOUT` | `float` | `30.0` | No | 30 |
| `DB_POOL_RECYCLE` | `int` | `1800` | No | 1800 |

SQLite (`sqlite:///...`) is only allowed in `development` and `testing` environments.

---

## Redis

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `REDIS_URL` | `str` | `redis://localhost:6379/0` | No (yes in production) | Set to production Redis with auth. Empty string disables Redis. |

Without Redis: cache returns `None`, rate limiting falls back to in-memory, worker returns no-op config.

---

## LLM

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `LLM_PROVIDER` | `str` | `groq` | No | `groq` or `openai` |
| `GROQ_API_KEY` | `str` | (empty) | **Yes** | Production API key from Groq console |
| `LLM_MODEL` | `str` | `llama-3.3-70b-versatile` | No | Production-optimized model |
| `LLM_MAX_TOKENS` | `int` | `4096` | No | 4096 |
| `LLM_TEMPERATURE` | `float` | `0.3` | No | 0.3 (lower = more deterministic) |
| `OPENAI_API_KEY` | `str` | (empty) | If `LLM_PROVIDER=openai` | OpenAI API key |

---

## Retrieval Providers

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `RETRIEVAL_PROVIDERS` | `str` | `semantic_scholar,arxiv,openalex` | No | Comma-separated list |

---

## Embeddings

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `EMBEDDING_PROVIDER` | `str` | `local` | No | Only `local` supported currently |
| `EMBEDDING_MODEL` | `str` | `all-MiniLM-L6-v2` | No | Sentence transformer model name |
| `EMBEDDING_DIMENSION` | `int` | `384` | No | Must match model output dimension |

The embedding model is downloaded on first use (sentence-transformers). Cache at `~/.cache/huggingface/hub/`.

---

## Cache

All cache TTLs are in seconds.

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `CACHE_ENABLED` | `bool` | `true` | No | `true` (requires Redis) |
| `CACHE_DEFAULT_TTL` | `int` | `300` | No | 300 (5 min) |
| `CACHE_GRAPH_TTL` | `int` | `1800` | No | 1800 (30 min) |
| `CACHE_LANDSCAPE_TTL` | `int` | `1800` | No | 1800 (30 min) |
| `CACHE_GAP_REPORT_TTL` | `int` | `1800` | No | 1800 (30 min) |
| `CACHE_KNOWLEDGE_PACKAGE_TTL` | `int` | `1800` | No | 1800 (30 min) |
| `CACHE_RETRIEVAL_TTL` | `int` | `600` | No | 600 (10 min) |
| `CACHE_INVESTIGATION_TTL` | `int` | `300` | No | 300 (5 min) |

---

## Rate Limiting

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `RATE_LIMIT_ENABLED` | `bool` | `true` | No | `true` |
| `RATE_LIMIT_BACKEND` | `str` | `redis` | No | `redis` (production) or `memory` (dev) |
| `DEFAULT_RATE_LIMIT` | `int` | `120` | No | 120 requests per window |
| `COPILOT_RATE_LIMIT` | `int` | `20` | No | 20 requests per window |
| `INVESTIGATION_RATE_LIMIT` | `int` | `10` | No | 10 requests per window |
| `RUN_RATE_LIMIT` | `int` | `5` | No | 5 pipeline runs per window |
| `RATE_LIMIT_WINDOW` | `int` | `60` | No | 60 seconds |

---

## Security

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `SECRET_KEY` | `str` | (empty) | **Yes** | Min 32 chars. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SECURITY_HEADERS_ENABLED` | `bool` | `true` | No | `true` |
| `REQUEST_TIMEOUT_SECONDS` | `float` | `30.0` | No | 30–60 |
| `MAX_REQUEST_SIZE` | `int` | `1048576` | No | 1 MB (1048576) |
| `MAX_JSON_SIZE` | `int` | `1048576` | No | 1 MB |
| `MAX_UPLOAD_SIZE` | `int` | `10485760` | No | 10 MB |
| `CSP_ENABLED` | `bool` | `true` | No | `true` |
| `CSP_DIRECTIVES` | `str` | `default-src 'self'; ...` | No | Customize for your frontend domain |

---

## Logging

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `LOG_FORMAT` | `str` | `console` | No | `json` in production (for log aggregators) |
| `LOG_LEVEL` | `str` | `INFO` | No | `INFO` or `WARNING` in production |

`LOG_FORMAT` values: `console` (human-readable with colors), `json` (structured JSON for log aggregation).

---

## CORS

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `CORS_ORIGINS` | `str` | `http://localhost:5173,http://localhost:3000,http://localhost:8000` | No | Your production frontend domain(s). No wildcards. |
| `CORS_ALLOWED_METHODS` | `str` | `GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD` | No | Restrict if needed |
| `CORS_ALLOWED_HEADERS` | `str` | `Authorization,Content-Type,X-Request-ID,...` | No | Default set covers common needs |
| `CORS_ALLOW_CREDENTIALS` | `bool` | `true` | No | `true` if using auth cookies |

---

## API

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `API_V1_PREFIX` | `str` | `/api/v1` | No | `/api/v1` |
| `TRUSTED_HOSTS` | `str` | `localhost,127.0.0.1` | No | Your production domain(s) |
| `OPENAPI_ENABLED` | `bool` | `true` | No | `false` in production (disable schema exposure) |
| `DOCS_ENABLED` | `bool` | `true` | No | `false` in production |
| `REDOC_ENABLED` | `bool` | `true` | No | `false` in production |

---

## Metrics

| Variable | Type | Default | Required | Production Recommendation |
|----------|------|---------|----------|--------------------------|
| `METRICS_ENABLED` | `bool` | `true` | No | `true` |
| `METRICS_PATH` | `str` | `/api/v1/metrics` | No | Keep as-is or change for ingress routing |
| `METRICS_NAMESPACE` | `str` | `resyntha` | No | Keep as-is |
| `METRICS_SUBSYSTEM` | `str` | `backend` | No | Keep as-is |
