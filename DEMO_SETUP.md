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

## Hybrid: API in Docker, UI local (auth debugging)

Use this when you want `docker compose logs -f api` while running Streamlit on the host.

```powershell
cd C:\_projects\_dev-roadmap\dev-roadmap

# Ensure .env exists and AUTHJWT_SECRET matches for UI + API
uv run scripts/run.py env

# Postgres + Qdrant + API container (rebuilds image)
uv run scripts/run.py api-docker

# Terminal A — API auth/access logs
docker compose logs -f api

# Terminal B — UI only (same root .env: AUTHJWT_SECRET + API_BASE_URL)
uv run scripts/run.py ui
```

Open http://localhost:8501 · sign in · submit analyze.

**What to compare in logs**

| Source | Line |
|--------|------|
| UI stdout | `[ui.auth] minted token … secret_len=… suffix=…` |
| `docker compose logs -f api` startup | `[auth] access-token secret loaded len=… suffix=…` |
| API on each request | `[app.auth] OK …` or `[app.auth] FAIL invalid signature …` |

`secret_len` and `suffix` must match. If they don’t, UI and container are not using the same `AUTHJWT_SECRET`.

Stop containers: `uv run scripts/run.py infra-down` (or `docker compose down`).

---

## Recommended: containers (DB/vector) + local API + local UI

Best layout for testing auth and watching API stdout:

```powershell
cd C:\_projects\_dev-roadmap\dev-roadmap

uv run scripts/run.py env
uv run scripts/run.py install
uv run scripts/run.py infra-up    # Postgres + Qdrant; frees :8000 if API container was up
uv run scripts/run.py migrate
uv run scripts/run.py seed-test

# Terminal 1 — local API (auth prints here)
uv run scripts/run.py api

# Terminal 2 — local UI
uv run scripts/run.py ui
```

Or one command after infra is ready: `uv run scripts/run.py dev`  
(`dev` runs `infra-up` then local API + UI.)

Uses root `.env`: `AUTHJWT_SECRET`, `API_BASE_URL=http://localhost:8000`, DB/Qdrant on `localhost`.

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
