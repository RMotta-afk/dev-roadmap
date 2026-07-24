# Demo Setup Guide

Run the **Agentic CV Analyzer** locally for a client deep-dive.

- Postgres + Qdrant in Docker
- FastAPI on port `8000`
- Streamlit UI on port `8501`
- Invite-only user ready to sign in

All orchestration is via **`uv run scripts/run.py`** (works on Windows without Make).

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.11 |
| uv | latest |
| Docker Desktop | any |

```powershell
python --version
uv --version
docker --version
```

---

## From zero (recommended)

```powershell
cd C:\_projects\_dev-roadmap\dev-roadmap
uv run scripts/run.py setup
```

Then one command (API + UI, shared env):

```powershell
uv run scripts/run.py dev
```

Open http://localhost:8501

---

## Manual steps

### 1. Environment

```powershell
uv run scripts/run.py env
```

Edit `.env` if needed (optional `LLM_API_KEY` for real LLM).

### 2. Dependencies

```powershell
uv run scripts/run.py install
```

### 3. Infrastructure

```powershell
uv run scripts/run.py infra-up
docker compose ps
```

### 4. Migrate + seed

```powershell
uv run scripts/run.py migrate
uv run scripts/run.py seed-test
```

Test user:

- **Email:** `mundo.dev@cv-analyzer.local`
- **Password:** `f3l!pe_p@llm@`

Custom admin:

```powershell
uv run scripts/run.py seed-admin
```

### 5. Servers

```powershell
# Terminal 1
uv run scripts/run.py api

# Terminal 2
uv run scripts/run.py ui
```

---

## Demo flow

1. Sign in with test credentials  
2. Submit CV form  
3. Watch SSE progress  
4. Review results (level, score, roadmap)  
5. Call out strict-subset guardrail  

---

## Stop

```powershell
# Ctrl+C on api/ui terminals
uv run scripts/run.py infra-down
# clean volumes:
docker compose down -v
```

---

## Quick reference

| What | Command |
|------|---------|
| Full setup | `uv run scripts/run.py setup` |
| Install | `uv run scripts/run.py install` |
| Infra up/down | `uv run scripts/run.py infra-up` / `infra-down` |
| Migrate | `uv run scripts/run.py migrate` |
| Seed test | `uv run scripts/run.py seed-test` |
| API | `uv run scripts/run.py api` |
| UI | `uv run scripts/run.py ui` |
| Lint | `uv run scripts/run.py lint` |
| Test | `uv run scripts/run.py test` |
