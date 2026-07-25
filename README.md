# CV Analyzer & Roadmap Generator

Restricted-access app that ingests an engineer's CV and description, runs an agentic analysis against a Base Roadmap, and returns a personalized development path.

**Stack:** Streamlit UI · FastAPI + LangGraph API · Postgres · Qdrant (pure Python; no Node).

## Project structure

- `apps/ui` — Streamlit frontend (login, CV form, SSE progress, results)
- `apps/api` — FastAPI + LangGraph backend
- `docs/archives` — Base roadmap JSON
- `docs/sql` — Postgres schema migrations
- `scripts/run.py` — cross-platform orchestration via `uv run`

## Quick start (from zero)

```powershell
# From repo root (PowerShell, CMD, or bash)
uv run scripts/run.py setup

# Docker: Postgres + Qdrant only
# Host:   local API :8000 + UI :8501 (same root .env)
uv run scripts/run.py dev
```

Open http://localhost:8501

Or step by step:

```powershell
uv run scripts/run.py env
uv run scripts/run.py install
uv run scripts/run.py infra-up   # Postgres + Qdrant (stops API container if it holds :8000)
uv run scripts/run.py migrate
uv run scripts/run.py seed-test

# Two terminals (or one):
uv run scripts/run.py api        # local FastAPI — watch auth logs here
uv run scripts/run.py ui         # Streamlit
# Or together:
uv run scripts/run.py dev
```

## Test user

After `seed-test`:

- Email: `mundo.dev@cv-analyzer.local`
- Password: `f3l!pe_p@llm@`

Custom admin:

```powershell
uv run scripts/run.py seed-admin
```

## Orchestration commands

| Command | Description |
|---------|-------------|
| `uv run scripts/run.py setup` | env + install + infra + migrate + seed-test |
| `uv run scripts/run.py env` | Copy `.env.example` → `.env` if missing |
| `uv run scripts/run.py install` | `uv sync` for api and ui |
| `uv run scripts/run.py infra-up` | Docker Postgres + Qdrant (stops container API) |
| `uv run scripts/run.py infra-down` | Stop Docker services |
| `uv run scripts/run.py migrate` | Apply `docs/sql` |
| `uv run scripts/run.py seed-test` | Create demo user |
| `uv run scripts/run.py seed-qdrant` | Seed Qdrant `roadmap_nodes` from `docs/archives` |
| `uv run scripts/run.py seed-qdrant --force` | Drop + re-seed Qdrant |
| `uv run scripts/run.py seed-admin` | Interactive admin user |
| `uv run scripts/run.py dev` | Infra + local API + UI (shared root `.env`) |
| `uv run scripts/run.py api` | Local FastAPI `:8000` only |
| `uv run scripts/run.py api-debug` | Local API + debugpy on `:5678` (no reload) |
| `uv run scripts/run.py ui` | Local Streamlit `:8501` only |
| `uv run scripts/run.py api-docker` | Optional: API inside Docker instead of host |
| `uv run scripts/run.py test` | Pytest both apps |
| `uv run scripts/run.py lint` | Ruff both apps |

## Environment

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | api, ui | Postgres DSN (`+asyncpg` ok; UI strips it) |
| `AUTHJWT_SECRET` | api, ui | Shared HMAC secret for API bearer tokens |
| `API_BASE_URL` | ui | FastAPI base URL (default `http://localhost:8000`) |
| `QDRANT_URL` / `QDRANT_API_KEY` | api | Vector store |
| `LLM_API_KEY` | api | OpenAI key; empty = mock mode |
| `LLM_MODEL` / `EMBEDDING_MODEL` | api | Model names |
| `CORS_ALLOW` | api | Optional browser origins |
| `BASE_ROADMAP_PATH` | api | Path to roadmap JSON (default `docs/archives`) |

## Deployment

- **API + UI:** Railway (two services), Dockerfiles under `apps/api` and `apps/ui`
- **DB:** Neon Postgres
- **Vectors:** Qdrant Cloud

See [`DEPLOYMENT_TASK.md`](./DEPLOYMENT_TASK.md).

## Demo

See [`DEMO_SETUP.md`](./DEMO_SETUP.md).
