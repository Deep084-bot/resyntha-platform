# Production Checklist

Use this checklist before deploying to production.

---

## Environment Configuration

- [ ] `ENVIRONMENT=production` — enables production validation
- [ ] `DATABASE_URL` points to production PostgreSQL (not SQLite)
- [ ] `REDIS_URL` is set to production Redis (not empty)
- [ ] `SECRET_KEY` is at least 32 characters, securely generated
- [ ] `TRUSTED_HOSTS` lists your production domains
- [ ] `CORS_ORIGINS` lists your frontend domain(s) (no wildcards)
- [ ] `GROQ_API_KEY` is a production API key (not a test/free key)
- [ ] `LOG_FORMAT=json` — structured logging for log aggregation
- [ ] `LOG_LEVEL=INFO` or `WARNING` (not `DEBUG`)
- [ ] `OPENAPI_ENABLED=false` — disable OpenAPI schema exposure
- [ ] `DOCS_ENABLED=false` — disable Swagger UI in production
- [ ] `REDOC_ENABLED=false` — disable ReDoc in production
- [ ] `CACHE_ENABLED=true` — requires Redis
- [ ] `RATE_LIMIT_ENABLED=true` — requires Redis
- [ ] `RATE_LIMIT_BACKEND=redis`

### Database Pool Tuning

Review and adjust:

- `DB_POOL_SIZE` — 20–50 depending on expected concurrency
- `DB_MAX_OVERFLOW` — 2× pool size
- `DB_POOL_TIMEOUT` — 30s
- `DB_POOL_RECYCLE` — 1800s (30 minutes)

---

## Database

- [ ] All migrations applied: `alembic upgrade head`
- [ ] Migration tested against a clean production-equivalent database
- [ ] Rollback plan documented: `alembic downgrade -1`
- [ ] Database backup configured (automated, daily)
- [ ] Database connection uses SSL/TLS
- [ ] Connection pooling configured (pool_size, max_overflow)
- [ ] PostgreSQL `max_connections` >= pool settings

---

## Testing

- [ ] All backend tests pass: `python -m pytest --cov=app`
- [ ] All frontend tests pass: `npx vitest run --coverage`
- [ ] Coverage meets threshold (configure `fail_under` in `pyproject.toml`)
- [ ] Health endpoints verified: `/health`, `/live`, `/ready`
- [ ] Metrics endpoint verified: `/metrics`
- [ ] Rate limiting confirmed working (rapid requests return 429)
- [ ] CORS confirmed working (frontend can reach backend)

---

## Linting & Type Checking

- [ ] Ruff check passes: `ruff check .`
- [ ] Ruff format check passes: `ruff format --check .`
- [ ] mypy passes: `mypy`
- [ ] oxlint passes: `npx oxlint .`
- [ ] TypeScript compiles: `npx tsc -b`

---

## Security

- [ ] `SECURITY_HEADERS_ENABLED=true`
- [ ] `CSP_ENABLED=true` and `CSP_DIRECTIVES` configured for your frontend
- [ ] `SECRET_KEY` is unique, long, and never committed to version control
- [ ] `.env` files are in `.gitignore`
- [ ] No secrets in code, logs, or error responses
- [ ] `MAX_REQUEST_SIZE` set appropriately (default 1 MB)
- [ ] `REQUEST_TIMEOUT_SECONDS` set appropriately (default 30s)
- [ ] Security headers verified via browser dev tools or security scanner
- [ ] pip audit passes: `pip-audit`
- [ ] npm audit passes: `npm audit --audit-level=moderate`
- [ ] GitLeaks scan passes (or reviewed): `gitleaks`

### CORS Hardening

- [ ] `CORS_ORIGINS` set to exact frontend domain(s), no wildcards
- [ ] `CORS_ALLOWED_METHODS` restricted to needed methods
- [ ] `CORS_ALLOWED_HEADERS` restricted to needed headers
- [ ] `CORS_ALLOW_CREDENTIALS` set appropriately

---

## Observability

- [ ] Logging configured with `LOG_FORMAT=json` for log aggregation
- [ ] Request logging active (all requests logged with duration, status, method, path)
- [ ] Metrics endpoint accessible and returns valid Prometheus data
- [ ] Health checks configured for load balancer / orchestration:
  - `/live` — liveness probe
  - `/ready` — readiness probe
- [ ] Cache monitoring: verify cache hit rates (if Redis available)
- [ ] Rate limit monitoring: verify rate limit counter behavior

---

## CI/CD

- [ ] Backend CI passes (Python 3.12 + 3.13 matrix)
- [ ] Frontend CI passes (Node 20 + 22 matrix)
- [ ] Quality checks pass (pip-audit, npm audit, gitleaks)
- [ ] CI runs on every push and PR
- [ ] CI blocks merge on failure (branch protection rules)
- [ ] Coverage artifacts generated and reviewable

---

## Deployment

- [ ] Database migrations run as part of deployment (before app starts)
- [ ] Environment variables injected via deployment platform (not `.env` files)
- [ ] Health checks configured in load balancer / orchestrator
- [ ] Graceful shutdown configured (SIGTERM handling)
- [ ] Logs shipped to centralized logging system
- [ ] Metrics scraped by monitoring system

---

## Monitoring (Post-Deployment)

- [ ] Verify `/health` returns all components healthy
- [ ] Verify API responses are not degraded (latency, error rate)
- [ ] Verify frontend loads and communicates with backend
- [ ] Verify copilot chat works and returns citations
- [ ] Verify pipeline execution works end-to-end
- [ ] Monitor error logs for unexpected issues
- [ ] Monitor cache hit rates and rate limit counters
- [ ] Set up alerts for:
  - Health check failures
  - Error rate spikes (>1% 5xx)
  - P95 latency > 5s
  - Rate limit threshold breaches
