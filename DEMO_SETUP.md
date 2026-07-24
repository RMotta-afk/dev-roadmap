# 🚀 Demo Setup Guide

This guide walks you through running the **Agentic CV Analyzer** locally for a
deep-dive presentation to the client. By the end you will have:

- Postgres + Qdrant running in Docker
- FastAPI backend serving on port `8000`
- Next.js frontend serving on port `3000`
- An admin user ready to sign in
- The full analysis pipeline working end-to-end

> **All commands below are identical on Windows, macOS, and Linux.**
> We use `pnpm` scripts with `concurrently` for cross-platform orchestration.

---

## Prerequisites

| Tool | Version | Install link |
|------|---------|--------------|
| Node.js | ≥ 18 | https://nodejs.org |
| pnpm | ≥ 9 | `npm install -g pnpm` |
| Python | ≥ 3.11 | https://python.org |
| uv | latest | `pip install uv` or https://docs.astral.sh/uv |
| Docker Desktop | any | https://docker.com/products/docker-desktop |

**Verify before you start:**

```bash
node --version    # v22.x or higher
pnpm --version    # 9.x or higher
python --version  # 3.11 or higher
uv --version      # any
docker --version  # Docker version 28.x
```

---

## 1. Start local infrastructure (Postgres + Qdrant)

Open a terminal in the **project root** and run:

```bash
pnpm infra:up
```

This starts:
- **Postgres** on `localhost:5432` (user: `cv_analyzer`, password: `localdev`, db: `cv_analyzer`)
- **Qdrant** on `localhost:6333`

Verify they are healthy:

```bash
docker-compose ps
# Both should show "healthy"
```

---

## 2. Install dependencies

In the project root:

```bash
pnpm install:all
```

What this does:
- `pnpm install` — installs Next.js, Drizzle, Auth.js, shadcn/ui, etc.
- `uv sync` — installs FastAPI, LangGraph, Qdrant client, asyncpg, etc.

---

## 3. Configure environment variables

Copy the local env template:

```bash
cp .env.local .env    # macOS / Linux / PowerShell
copy .env.local .env  # Windows CMD
```

The `.env` file already contains sensible **local-only** defaults.  
You only need to change something if:
- You moved the Docker ports
- You want to use a real OpenAI key for better LLM results (optional)

---

## 4. Run database migrations

```bash
pnpm db:push
```

Creates `users` and `analyses` tables in the local Postgres.

---

## 5. Seed a user

### Option A — Quick test user (recommended for demos)
```bash
pnpm db:seed-test
```

This creates the pre-configured test user:
- **Email:** `mundo.dev@cv-analyzer.local`
- **Password:** `f3l!pe_p@llm@`
- **Name:** Mundo Dev
- **Role:** Admin

### Option B — Create a custom admin user
```bash
pnpm db:seed-admin
```

Follow the prompts: enter any email and password you choose.

**No public sign-up page exists** — this is an invite-only app.

---

## 6. Start the dev servers

```bash
pnpm dev
```

You will see:
- Backend: `Uvicorn running on http://0.0.0.0:8000`
- Frontend: `Ready on http://localhost:3000`

Open the frontend URL in your browser.

---

## 7. Demo flow for the client

### 7.1 Sign in
- Navigate to `http://localhost:3000`
- You will be redirected to `/sign-in`
- Enter the admin email + password you created in Step 5

### 7.2 Submit a CV
- On the home page, fill in:
  - **Name:** any demo name
  - **Phone:** any number
  - **Email:** any email
  - **Description:** a brief self-description (e.g., "Senior backend engineer with 5 years Python and AWS experience")
  - **CV:** upload a plain `.txt` file with skills/experience (PDF support is a post-MVP feature)
- Click **Analyze**
- The app navigates to `/analyze/<id>` and shows a **streaming progress panel**

### 7.3 Watch the agent work
The progress panel shows each LangGraph node completing:
1. `ingest` — ingests the file
2. `strip` — extracts text
3. `analyze` — LLM extracts skills (uses **mock extraction** if no OpenAI key, or real GPT if key is set)
4. `compare` — RAG retrieves relevant Base Roadmap nodes
5. `level_guess` — estimates seniority + compatibility score
6. `roadmap_select` — builds the personalized roadmap

### 7.4 Review results
When complete, the **Results View** shows:
- **Level Resume:** strong points, weak points, estimated level (junior / mid / senior / staff)
- **Compatibility Score:** 0-100 alignment with the Base Roadmap
- **Personalized Roadmap:** a filtered list of Base Roadmap nodes addressing identified gaps

### 7.5 Strict-subset guardrail (ADR-008)
If you want to highlight the key business rule:
> "The personalized roadmap is **never invented** by the AI. It is strictly a subset of our curated Base Roadmap. Every item is validated against the canonical index before it reaches the user."

---

## 8. Switching to real LLM (optional)

For a more impressive demo, set a real OpenAI API key:

1. Open `.env`
2. Set `LLM_API_KEY=sk-your-key-here`
3. Restart the backend (`Ctrl+C` then re-run `pnpm dev`)

The `analyze` node will now use GPT-4o-mini (or your chosen model) for structured skill extraction instead of the deterministic mock.

---

## 9. Stopping everything

```bash
# Stop dev servers
Ctrl+C in the terminal

# Stop Docker infrastructure
pnpm infra:down

# To also delete data volumes (clean slate)
docker-compose down -v
```

---

## Troubleshooting

### Port already in use
- **3000:** kill any other Next.js process, or set `PORT=3001` before running
- **8000:** kill any other Python server, or edit `pnpm dev:api`
- **5432 / 6333:** ensure Docker containers from a previous run were stopped (`pnpm infra:down`)

### Qdrant not reachable
The app gracefully skips seeding if Qdrant is down. For the demo, ensure Docker is running:
```bash
docker-compose ps
```

### Database connection refused
Ensure Postgres is healthy:
```bash
docker-compose logs postgres
```

### Auth issues (JWT mismatch)
Ensure `AUTH_SECRET` and `AUTHJS_JWT_SECRET` in `.env` are **identical**.

---

## Quick reference

| What | Command |
|------|---------|
| Install deps | `pnpm install:all` |
| Start infra | `pnpm infra:up` |
| DB migrate | `pnpm db:push` |
| Seed test user | `pnpm db:seed-test` |
| Seed custom admin | `pnpm db:seed-admin` |
| Start dev | `pnpm dev` |
| Stop infra | `pnpm infra:down` |
| Lint | `pnpm lint` |
| Test | `pnpm test` |

---

## Support

If anything breaks during the demo setup, check:
1. `.env` exists and has all variables
2. Docker Desktop is running
3. `pnpm --version` and `uv --version` return valid versions
4. `docker-compose ps` shows both services healthy

> Last updated: 2026-07-24
