# Development Guide

---

## Branching Strategy

```
main          Production-ready releases
develop       Integration branch for features
feat/*        Feature branches (e.g., feat/paper-batching)
fix/*         Bug fixes (e.g., fix/cache-key-collision)
docs/*        Documentation changes
chore/*       Tooling, dependencies, CI
```

- Create feature branches from `develop`
- Open PRs targeting `develop`
- Merge `develop` into `main` for releases

---

## Commit Conventions

Use conventional commits:

```
feat: add paper batching to retrieval coordinator
fix: correct cache key collision in investigation service
docs: update API reference for copilot streaming
chore: upgrade ruff to 0.9.0
refactor: extract embedding provider interface
test: add security header tests for CSP directives
ci: add Python 3.13 to backend matrix
```

---

## Testing

### Backend

```bash
# Run all tests
cd backend && python -m pytest

# With coverage
python -m pytest --cov=app --cov-report=term

# Specific test file
python -m pytest tests/test_security.py -v

# Skip PostgreSQL-dependent tests
python -m pytest -k "not postgresql"

# Run with warnings
python -m pytest -W ignore::DeprecationWarning
```

### Frontend

```bash
# Run all tests
cd frontend && npx vitest run

# Watch mode
npx vitest

# With coverage
npx vitest run --coverage
```

### Linting

```bash
# Backend (Ruff)
cd backend && ruff check .
ruff format --check .

# Frontend (oxlint)
cd frontend && npx oxlint .
```

### Type Checking

```bash
# Backend (mypy)
cd backend && mypy

# Frontend (TypeScript)
cd frontend && npx tsc -b
```

---

## Adding a New Module

1. Create the module directory structure:

```
modules/<name>/
├── __init__.py
├── domain/            # SQLAlchemy models, enums
├── service/           # Business logic
├── api/               # FastAPI routes
├── schemas/           # Pydantic models
└── repository/        # Data access layer
```

2. If the module needs database models:
   - Add models in `domain/`
   - Register in `app/database/model_registry.py` (if using the registry pattern)
   - Create an Alembic migration: `cd backend && alembic revision --autogenerate -m "add <name> tables"`
   - Review and apply: `alembic upgrade head`

3. If the module needs API routes:
   - Create routes in `api/routes.py`
   - Add the router to `app/api/v1/__init__.py`

4. Add tests in `backend/tests/`

5. Add new services to `app/plugins/wrappers.py` if they should be pipeline stages.

---

## Adding a New Route

1. Find the appropriate module's `api/routes.py`
2. Create the route function with `@router.get/post/...`
3. Inject dependencies via `Depends()`:
   - `Session` for database access
   - `Settings` via `get_settings()` for configuration
   - `CacheService` via `get_cache_service()` for caching
4. Define request/response schemas in the module's `schemas/` directory
5. Add the route to the API reference in `docs/api.md`

---

## Adding Middleware

1. Create the middleware class in `app/core/middleware/`
2. Implement `__init__(self, app)` and `__call__(self, scope, receive, send)`
3. Register in `app/main.py::create_app()` using `app.add_middleware()`
4. Respect the execution order documented in `app/main.py`
5. Add tests in `backend/tests/`
6. Document in `docs/architecture.md`

---

## Database Migrations

```bash
# Auto-generate migration from model changes
cd backend && alembic revision --autogenerate -m "description"

# Review generated migration in alembic/versions/
# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View history
alembic history
```

Migration conventions:
- Always review auto-generated migrations before applying
- Name migrations descriptively (e.g., `add_copilot_tables`)
- Never edit applied migrations — create a new one

---

## Workers

### Adding a Job

1. Create the job function in `app/workers/<name>_job.py`
2. Add it to the `FUNCTIONS` list in `app/workers/worker.py`
3. Enqueue from async context:

```python
from app.workers.worker import enqueue_job
await enqueue_job("my_job", arg1, arg2)
```

### Running the Worker

```bash
# Start worker (from backend directory)
python -m app.workers.worker

# Or use the ARQ CLI
arq app.workers.worker.WorkerSettings
```

---

## Repositories

Repository pattern wraps SQLAlchemy queries:

```python
class PaperRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, paper_id: uuid.UUID) -> Paper | None:
        return self._session.get(Paper, paper_id)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> list[Paper]:
        return (
            self._session.execute(
                select(Paper).join(InvestigationPaper).where(
                    InvestigationPaper.investigation_id == investigation_id
                )
            )
            .scalars()
            .all()
        )
```

Repository methods should:
- Accept and return domain models (not dicts)
- Be composable (not include business logic)
- Have clear, descriptive names

---

## Dependency Injection Pattern

Route handlers use `Depends()` for service wiring:

```python
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db

def get_investigation_service(db: Session = Depends(get_db)) -> InvestigationService:
    return InvestigationService(db)

@router.get("/investigations/{id}")
def get_investigation(
    id: uuid.UUID,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    return service.get_investigation(id)
```

For config, use the cached singleton directly:

```python
from app.config import get_settings

settings = get_settings()
```
