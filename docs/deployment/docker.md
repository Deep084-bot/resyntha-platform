# Docker Deployment

## Quick Start

```bash
docker compose up --build
```

This starts:
| Service     | Port     | Notes                          |
|-------------|----------|--------------------------------|
| PostgreSQL  | `:5432`  | Persistent volume              |
| Redis       | `:6379`  | Persistent volume              |
| Backend     | `:8000`  | FastAPI + Uvicorn              |
| Worker      | —        | ARQ background worker          |
| Frontend    | `:80`    | Nginx serving SPA + API proxy  |

Open [http://localhost](http://localhost) for the application.  
View API docs at [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs).

## Architecture

```
Browser ──► Nginx (:80) ──► /api/* ──► Backend (:8000)
                │                        │
                │                        ├── PostgreSQL (:5432)
                │                        └── Redis (:6379)
                │
                └── SPA (static files)
                                    Worker (ARQ) ──► Redis
```

Services are connected through a shared `resyntha` bridge network.
Data volumes (`postgres_data`, `redis_data`) persist across restarts.

## Multi-stage Builds

### Backend (`backend/Dockerfile`)

| Stage    | Base              | Purpose                              |
|----------|-------------------|--------------------------------------|
| `builder`| `python:3.12-slim`| Install build deps + Python packages |
| `runtime`| `python:3.12-slim`| Minimal runtime with venv + app code |

- Runs as non-root `appuser` (uid 1000)
- Healthcheck: `GET /api/v1/live` every 30s

### Frontend (`frontend/Dockerfile`)

| Stage    | Base                | Purpose                          |
|----------|---------------------|----------------------------------|
| `builder`| `node:22-alpine`    | `npm ci` + `npm run build`       |
| `runtime`| `nginx:alpine`      | Serves built assets via nginx    |

- `VITE_API_URL` build arg: set to empty for same-origin (nginx proxy), or a full URL for direct backend access
- Custom `nginx.conf` handles SPA routing and proxies `/api/` to the backend service

## Environment Files

| File                           | Used By              | Purpose                           |
|--------------------------------|----------------------|-----------------------------------|
| `backend/.env.docker`          | docker-compose       | Default Docker environment        |
| `backend/.env.development`     | Dev script (host)    | Local development                 |
| `backend/.env.production.example` | Manual copy       | Production template               |
| `backend/.env.testing`         | pytest               | Test environment (SQLite)         |

Override any value by setting it in your shell or creating a `docker-compose.override.yml`.

## Commands

```bash
# Build and start all services
docker compose up --build

# Start in detached mode
docker compose up --build -d

# View logs
docker compose logs -f

# Run migrations
docker compose exec backend alembic upgrade head

# Run tests
docker compose exec backend python -m pytest

# Run a shell in the backend container
docker compose exec backend bash

# Stop all services
docker compose down

# Stop and remove volumes (destroys data)
docker compose down -v

# Rebuild a single service
docker compose build backend
```

## Development Mode

The `docker-compose.override.yml` is loaded automatically when present.
It enables:

- **Backend**: `--reload` for hot-reload on code changes, mounts `app/` and `alembic/`
- **Frontend**: Sets `VITE_API_URL` to `http://localhost:8000/api/v1` for direct API access during dev
- **Worker**: `--watch` for auto-reload

To use the dev overrides with a different env file:

```bash
docker compose -f docker-compose.yml -f my-override.yml up --build
```

## Production Checklist

1. Generate a secure `SECRET_KEY`: `openssl rand -hex 32`
2. Set `ENVIRONMENT=production` and `DEBUG=false`
3. Set strong `POSTGRES_PASSWORD`
4. Update `CORS_ORIGINS` to your domain
5. Update `TRUSTED_HOSTS` to your domain
6. Set `LOG_FORMAT=json` for structured logging
7. Disable docs: `OPENAPI_ENABLED=false`, `DOCS_ENABLED=false`, `REDOC_ENABLED=false`
8. Add `GROQ_API_KEY` (or `OPENAI_API_KEY`)
9. Use managed PostgreSQL and Redis for production (set `DATABASE_URL` and `REDIS_URL`)
10. Configure a reverse proxy (e.g., Caddy, Traefik, or cloud LB) for TLS termination

## Troubleshooting

### Backend fails to start

Check logs: `docker compose logs backend`

Common causes:
- PostgreSQL not ready yet (container waits 60s by default)
- Missing `GROQ_API_KEY` (LLM health check fails but app still starts)
- Port 8000 already in use

### Frontend shows blank page

Check browser console for CORS errors or 404 on API calls.
If `VITE_API_URL` is set, ensure it points to the correct backend URL.
If empty, ensure nginx proxy is working: `curl http://localhost/api/v1/health`

### Worker not processing jobs

Check logs: `docker compose logs worker`
Ensure Redis is accessible: `docker compose exec redis redis-cli ping`
