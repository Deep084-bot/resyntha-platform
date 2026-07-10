# Troubleshooting Guide

---

## Redis Unavailable

**Symptom**: Cache returns None, rate limiting uses in-memory backend, worker logs connection errors.

**Cause**: `REDIS_URL` is empty or Redis server is not running.

**Check**:
```bash
# Is Redis running?
redis-cli ping

# Is REDIS_URL set?
grep REDIS_URL .env
```

**Fix**: Start Redis (`brew services start redis` on macOS) or set `REDIS_URL` to empty string to disable Redis features gracefully. The application runs without Redis — cache degrades, rate limiting falls back to in-memory, worker returns no-op config.

**Does not affect**: Health checks (Redis shows as unavailable), API routes (no hard dependency).

---

## Embedding Model Missing

**Symptom**: `SentenceTransformer` download hangs or fails on first request. Copilot returns "No embeddings found" or semantic retrieval errors.

**Cause**: The `all-MiniLM-L6-v2` model is not cached locally and cannot be downloaded.

**Check**:
```bash
# Check HuggingFace cache
ls ~/.cache/huggingface/hub/ | grep MiniLM
```

**Fix**: Pre-download the model:
```python
from sentence_transformers import SentenceTransformer
SentenceTransformer("all-MiniLM-L6-v2")
```

Or set `EMBEDDING_MODEL` to an already-available model.

---

## Migration Failure

**Symptom**: `alembic upgrade head` fails with relationship/key errors.

**Cause**: Migration ordering, existing data conflicts, or missing dependencies.

**Check**:
```bash
# Current revision
alembic current

# Migration history
alembic history
```

**Fix**:
```bash
# Roll back and retry
alembic downgrade -1
alembic upgrade head

# If starting fresh, reset
alembic downgrade base
alembic upgrade head
```

For persistent issues, check the migration file for correctness. Auto-generated migrations may need manual adjustment for complex operations.

---

## Worker Not Starting

**Symptom**: Jobs remain in "pending" state. Worker logs show connection errors.

**Cause**: Redis unavailable, ARQ import errors, or function reference issues.

**Check**:
```bash
# Test Redis
redis-cli ping

# Test worker import
python -c "from app.workers.worker import WorkerSettings; print('OK')"

# Test job function
python -c "from app.workers.retrieval_job import retrieval_job; print('OK')"
```

**Common fixes**:
- Ensure `REDIS_URL` is set and Redis is running
- Check that all job functions are listed in `WorkerSettings.FUNCTIONS`
- Verify no syntax errors in job files
- Check worker logs for import errors

---

## SentenceTransformer Download Issues

**Symptom**: Long download times, SSL errors, or connection timeouts when loading the embedding model.

**Cause**: Network restrictions, missing dependencies, or HuggingFace connectivity issues.

**Fix**:
```bash
# Set HuggingFace mirror (China)
export HF_ENDPOINT=https://hf-mirror.com

# Install build dependencies (Ubuntu/Debian)
sudo apt-get install -y build-essential

# Use a different model
export EMBEDDING_MODEL=all-MiniLM-L12-v2
```

---

## Cache Disabled

**Symptom**: Every request hits the database or external APIs. `@cached` decorators log "cache_write_failed" or "cache_read_failed".

**Cause**: `CACHE_ENABLED=false` or Redis unavailable.

**Check**:
```bash
grep CACHE_ENABLED .env
```

**Fix**: Set `CACHE_ENABLED=true` and ensure `REDIS_URL` is configured. The application degrades gracefully without cache.

---

## Rate Limit Fallback

**Symptom**: Rate limiting works but logs show "using in-memory backend".

**Cause**: `RATE_LIMIT_BACKEND=memory` or Redis unavailable with `RATE_LIMIT_BACKEND=redis`.

**Check**:
```bash
grep RATE_LIMIT_BACKEND .env
```

**Fix**: Set `RATE_LIMIT_BACKEND=redis` and ensure Redis is available. In-memory backend is suitable for development but resets on server restart.

---

## Health Endpoint Failures

**Symptom**: `/health` or `/ready` return partial/failure status.

**Common causes**:

| Component | Likely Issue |
|-----------|-------------|
| Database | PostgreSQL not running, wrong `DATABASE_URL`, migration not applied |
| Redis | Redis not running, wrong `REDIS_URL`, auth mismatch |
| LLM | `GROQ_API_KEY` missing or invalid |
| Embeddings | Model not downloaded |
| Worker | ARQ import error, Redis unavailable |

**Check each**:
```bash
# Database
psql "$DATABASE_URL" -c "SELECT 1"

# Redis
redis-cli ping

# LLM
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | head
```

---

## CORS Errors (Frontend)

**Symptom**: Browser console shows CORS errors when the frontend calls the API.

**Cause**: `CORS_ORIGINS` does not include the frontend's origin.

**Check**:
```bash
grep CORS_ORIGINS .env
```

**Fix**: Add the frontend URL to `CORS_ORIGINS`:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com
```

---

## Secret Key Validation

**Symptom**: Server fails to start with "SECRET_KEY must be at least 32 characters in production".

**Cause**: `ENVIRONMENT=production` with a short `SECRET_KEY`.

**Fix**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output to `SECRET_KEY` in your `.env.production`.

---

## Generic 500 Errors

**Symptom**: API returns 500 with no detail.

**Cause**: Intentionally — in production, internal errors return no detail to avoid information leakage.

**Check server logs**:
```bash
# If LOG_FORMAT=json
tail -f backend.log | grep "500"

# If LOG_FORMAT=console
uvicorn app.main:app  # watch stderr
```

**Fix**: Set `DEBUG=true` temporarily for development debugging (never in production).
