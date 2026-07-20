# Contributing to Resyntha

Thank you for considering contributing to Resyntha — we welcome all contributions, whether it's a bug report, feature suggestion, documentation improvement, or code contribution.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Feature Requests](#feature-requests)
- [Documentation](#documentation)

---

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to uphold its terms.

---

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/resyntha.git`
3. Follow the [setup guide](docs/setup.md) to configure your environment
4. Run the tests to verify everything works: `cd backend && python -m pytest`
5. Create a feature branch: `git checkout -b feat/my-feature`

---

## Development Workflow

### Branch Naming

| Prefix   | Purpose           | Example                    |
|----------|-------------------|----------------------------|
| `feat/`  | New features      | `feat/paper-batching`      |
| `fix/`   | Bug fixes         | `fix/cache-key-collision`  |
| `docs/`  | Documentation     | `docs/api-streaming`       |
| `chore/` | Tooling, deps, CI | `chore/upgrade-ruff`       |
| `refactor/` | Code restructuring | `refactor/extract-provider` |

### Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat: add paper batching to retrieval coordinator
fix: correct cache key collision in investigation service
docs: update API reference for copilot streaming
chore: upgrade ruff to 0.9.0
```

### Workflow Steps

1. Branch from `develop` for features and fixes
2. Make changes following the [code standards](#code-standards)
3. Write or update tests
4. Run the full test suite locally
5. Push and open a pull request against `develop`
6. Address review feedback
7. Squash merge when approved

---

## Code Standards

### Python (Backend)

- **Style**: Ruff default rules (E, F, I, N, W, UP)
- **Line length**: 100 characters
- **Quotes**: Double quotes (`"`)
- **Type hints**: Required for all function signatures
- **Formatting**: `ruff format` enforced in CI

Run checks before committing:

```bash
cd backend
ruff check .
ruff format --check .
mypy app/
```

### TypeScript (Frontend)

- **Mode**: Strict mode
- **Target**: ES2023
- **Linting**: oxlint (`npm run lint`)
- **Formatting**: Prettier (default config)

Run checks:

```bash
cd frontend
npm run lint
npx tsc -b
```

### Module Structure

Every backend module follows this convention:

```
modules/<name>/
├── domain/          # SQLAlchemy ORM models, enums, value objects
├── service/         # Business logic, orchestrators
├── api/             # FastAPI route definitions
├── schemas/         # Pydantic request/response models
└── repository/      # SQLAlchemy data access layer
```

### Pipeline Stages

Extend `PipelineStage` and declare `consumes` and `produces`:

```python
class MyStage(PipelineStage):
    id = "my_stage"
    consumes = {ArtifactType.SOME_INPUT}
    produces = {ArtifactType.MY_OUTPUT}

    async def __call__(self, context: PipelineContext) -> PipelineResult:
        ...
```

### General Rules

- No commented-out code
- No untracked `.env` files
- No secrets in code, logs, or error responses
- All public functions and classes have docstrings
- Follow existing patterns in the codebase

---

## Testing

### Backend

```bash
# Full suite
cd backend && python -m pytest

# With coverage
python -m pytest --cov=app --cov-report=term

# Specific file
python -m pytest tests/test_security.py -v

# Skip PostgreSQL-dependent tests
python -m pytest -k "not postgresql"
```

### Frontend

```bash
cd frontend
npx vitest run
npx vitest run --coverage
npx vitest       # watch mode
```

### Before Submitting

- [ ] All tests pass
- [ ] New tests cover the changes
- [ ] Ruff check passes (`ruff check .`)
- [ ] Ruff format passes (`ruff format --check .`)
- [ ] mypy passes (`mypy app/`)
- [ ] oxlint passes (`npm run lint`)
- [ ] TypeScript compiles (`npx tsc -b`)

---

## Pull Request Process

1. **Title**: Use conventional commit format (e.g., `feat: add paper batching`)
2. **Description**: Describe what the PR does and why
3. **Related issues**: Link to any related issues (e.g., `Closes #42`)
4. **Checklist**: Verify the checklist in the PR template
5. **Review**: At least one maintainer review required
6. **Merge**: Squash merge into `develop`

See [PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) for the PR template.

---

## Issue Guidelines

Before opening an issue:
- Search existing issues to avoid duplicates
- Use the appropriate [issue template](.github/ISSUE_TEMPLATE/)
- Provide reproduction steps for bugs
- Include environment details (Python version, OS, etc.)

Issue types:
- **Bug report**: Unexpected behavior, crashes, incorrect results
- **Feature request**: New functionality or enhancements
- **Question**: Usage questions, clarification

---

## Feature Requests

Feature requests are welcome. To increase the chances of acceptance:

1. Explain the problem you're solving, not just the solution
2. Describe how it fits into the existing architecture
3. Offer implementation hints if you have them
4. Be open to alternative approaches

Large features should be discussed in an issue before implementation.

---

## Documentation

Documentation improvements are highly valued. Areas that always need help:

- Fixing typos or broken links
- Clarifying ambiguous sections
- Adding examples and use cases
- Translating to other languages (future)
- API reference completeness

All documentation is in Markdown under `docs/`.

---

## Need Help?

- Check [docs/setup.md](docs/setup.md) for environment setup
- Check [docs/troubleshooting.md](docs/troubleshooting.md) for common issues
- Open a [discussion](https://github.com/anomalyco/resyntha/discussions)

Thank you for contributing!
