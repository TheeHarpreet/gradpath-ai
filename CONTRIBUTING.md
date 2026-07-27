# Contributing to GradPath AI

## Development principles

- Work from an issue or a clearly documented requirement.
- Keep candidate claims traceable to evidence.
- Never commit real CVs, contact details, credentials, or provider responses.
- Add or update tests with every behaviour change.
- Record material architectural changes as ADRs.
- Keep AI-generated changes small enough to review and understand.

## Prerequisites

- Python 3.13
- Node.js 20.19 or newer compatible release
- npm
- uv
- Git
- Docker with Compose for the local database (not required for current scaffold
  tests)

## Setup

```powershell
python -m uv sync --locked --all-packages --dev
npm ci --prefix apps/web
Copy-Item .env.example .env
```

## Run locally

API:

```powershell
python -m uv run gradpath-api
```

Web application:

```powershell
npm --prefix apps/web run dev
```

MCP adapter:

```powershell
python -m uv run gradpath-mcp
```

The MCP adapter intentionally exposes no domain tools until Step 6.

## Quality checks

```powershell
python -m uv run ruff format --check .
python -m uv run ruff check .
python -m uv run mypy
python -m uv run pytest
npm --prefix apps/web run check
```

## Git workflow

1. Create a focused branch from `main`.
2. Make small, reviewable changes.
3. Run all relevant checks.
4. Commit with a concise description.
5. Push the branch and open a draft pull request.
6. Explain what changed, why, validation performed, and remaining limitations.

