# Setup Guide

## Prerequisites

- **Python** >= 3.12
- **Node.js** >= 22
- **PostgreSQL** >= 15
- **Redis** >= 7
- **Docker** (optional, for containerized setup)

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/anomalyco/resyntha.git
cd resyntha
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies (including dev)
pip install -e ".[dev]"

# Create environment file
cp .env.example .env
```

### 3. Database Setup

```sql
CREATE DATABASE resyntha;
```

Then apply migrations:

```bash
cd backend
alembic upgrade head
```

### 4. Redis Setup

```bash
# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt install redis-server && sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Frontend Setup

```bash
cd frontend
npm install
```

---

## Docker Setup

The simplest way to start all services:

```bash
docker compose up --build
```

See [docs/deployment/docker.md](deployment/docker.md) for detailed Docker instructions.

---

## Configuration

Edit `backend/.env` with your settings. Required variables:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | API key for LLM provider (Groq) |
| `SECRET_KEY` | Secret for HMAC signing (min 32 chars in production) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

See [docs/environment.md](environment.md) for the complete variable reference.

---

## Verification

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Open [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) — should return `{"status": "healthy"}`.

Start the frontend:

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — the application should load.

Run the tests:

```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npx vitest run
```

---

## Next Steps

- [Development Guide](development.md) — commit conventions, adding modules, testing
- [API Reference](api.md) — full endpoint documentation
- [Architecture](architecture.md) — pipeline engine, copilot, intelligence engine
- [Troubleshooting](troubleshooting.md) — common issues and solutions
