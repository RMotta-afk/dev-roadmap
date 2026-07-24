# Software Design Document — Agentic CV Analyzer & Roadmap Generator

This SDD is the agent's semantic memory. Every Task in the decomposition DAG
must map to a component, schema, contract, or pattern defined here. Nothing
may be introduced outside this document. Architecture decisions are locked in
`.context/decisions.md` (ADRs); this document expands them into a buildable
specification.

---

## 1. System Overview

A restricted-access web application that ingests an engineer's CV + brief
description, runs an agentic analysis against a Base Roadmap of expected
engineering abilities, and returns a personalized development path that is a
strict subset of the Base Roadmap.

- Access: invite-only (admin-created users, no self-signup), auth-gated routes.
- Non-functional: free/starter-tier hosting only, one backend service, no
  queues, no GPU, structured logs.

---

## 2. Monorepo Structure

```
/
├─ apps/
│  ├─ ui/                 # Streamlit frontend (Python, uv)
│  └─ api/                # FastAPI + LangGraph (Python, uv)
├─ docs/
│  ├─ archives/           # Base Roadmap JSON files (source of truth)
│  ├─ sql/                # Postgres schema migrations
│  └─ sdd/                # this document
├─ .context/
│  ├─ project_context.md
│  ├─ decisions.md
│  └─ decomposition.json
├─ scripts/run.py         # uv run orchestration (Windows-friendly)
├─ docker-compose.yml
└─ .gitignore
```

**Tooling decisions:** pure Python monorepo via uv; `scripts/run.py` for
orchestration (no Make/Node).

---

## 3. Component Inventory

| ID | Component | Responsibility | SDD § |
|----|-----------|----------------|-------|
| C-FE | Frontend (apps/ui) | Streamlit UI, auth gate, form / progress / results | §4 |
| C-AUTH | Auth subsystem | Streamlit login, argon2 + Postgres users, HS256 JWT mint for API | §5 |
| C-API | Backend FastAPI | REST + SSE, Pydantic DTOs, CORS, JWT verify, logging | §6 |
| C-DATA | Base Roadmap data layer | JSON loader, Pydantic models, in-memory node index | §7 |
| C-RAG | RAG / Qdrant | Ingestion, embedding, startup seeder, hybrid retriever | §8 |
| C-AGENT | Agentic LangGraph | Graph nodes + strict-subset guardrail + structured output | §9 |
| C-DB | Relational store (Neon) | users, analyses tables | §10 |
| C-DEPLOY | Deployment | Dockerfiles, Railway (api + ui), env, README | §11 |

---

## 4. Frontend (C-FE)

- **Stack:** Streamlit (Python), server-side httpx to FastAPI.
- **Surfaces (session-state pages):**
  - Sign-in — public; no signup.
  - Home — protected CV + description form.
  - Progress — SSE stream of agent steps.
  - Results — level resume, score, personalized roadmap.
- **Shell:** brand header, sign-out, main content, footer caption.
- **Theme:** `.streamlit/config.toml` dark tokens (approximate prior design).
- **API integration:** `ui.api.client` posts multipart `/analyze` and consumes
  `/analyze/{id}/events` SSE; DTOs mirrored from FastAPI Pydantic schemas.

---

## 5. Auth Subsystem (C-AUTH)

- **Provider:** Streamlit form + Postgres `users` lookup.
- **Password hashing:** argon2-cffi.
- **Session:** Streamlit `st.session_state` after successful login.
- **API bridge:** UI mints short-lived HS256 JWT (`sub`, `email`, `is_admin`)
  with `AUTHJWT_SECRET` matching the API verifier.
- **Public surface:** only sign-in. No self-signup.
- **Invite flow:** `apps/ui/scripts/create_user.py` (and seed_test_user).
- **Backend verification (C-API):** FastAPI `HTTPBearer` JWT HS256 dependency;
  protected endpoints return 401 if invalid/expired.

---

## 6. Backend FastAPI (C-API)

- **App factory:** `create_app()` producing the FastAPI instance.
- **Middleware:** CORS allowlist (Streamlit origin + localhost), structured JSON
  logging with request-id, JWT verification dependency.
- **Endpoints:**
  - `GET /healthz` — unauthenticated liveness probe.
  - `POST /analyze` — accepts multipart form (DTO §6 of project_context),
    echoes a `201` with `analysis_id`, then begins streaming agent progress.
  - `GET /analyze/{id}/events` — SSE stream delivering node-progress events
    + final result DTO.
- **Pydantic v2 DTOs:** `AnalyzeRequest`, `AnalyzeResponse`, `RoadmapNode`,
  `LevelResume`, `AgentProgressEvent`.
- **Settings:** pydantic-settings loading env vars (Qdrant URL/key, Neon DSN,
  JWT secret, embedding model, LLM provider/key).
- **Startup hook:** invoke C-RAG seeder (idempotent) before serving.

---

## 7. Base Roadmap Data Layer (C-DATA)

- **Source files:** `docs/archives/*.json` (12 files across 3 roles × 4 levels).
- **Pydantic models:** `RoadmapFile`, `RoadmapNode` (id, name, type, category,
  level, importance, aliases, requirements_by_level, content_guidance,
  interview), `requirements_by_level` typed per level dict.
- **Loader:** reads all JSONs into a `RoadmapIndex` keyed by `node_id`,
  with reverse lookup by `role` + `level` + `category`. Loaded once at
  startup; cached in-memory.
- **Validator:** `is_valid_subset(node_ids: list[str]) -> bool` — the single
  source of truth for the strict-subset rule (ADR-008).

---

## 8. RAG / Qdrant (C-RAG)

- **Client:** `qdrant-client` async, pointing at Qdrant Cloud.
- **Collection:** `roadmap_nodes`. Points: payload
  `{role, level, node_id, category, importance, name, description, content_guidance}`.
  One collection, filtered queries.
- **Embeddings:** text-embedding model (configurable; default OpenAI
  `text-embedding-3-small` or local fallback). Embedding service abstracted
  behind an interface so model can change without touching the rest.
- **Startup seeder (ADR-006):** idempotent — if collection point count == 0,
  parse Base Roadmap via C-DATA, embed each node's name+description+topics,
  upsert. Otherwise skip.
- **Retriever:** hybrid search (dense vector + sparse keyword/alias match)
  with filters `{role, level}`; returns candidate `RoadmapNode`s ranked by
  relevance. Tunable top-k.

---

## 9. Agentic Layer — LangGraph (C-AGENT)

- **State schema:** `AgentState { user_id, raw_cv_text, raw_description,
  extracted_skills, matched_nodes, level_estimate, compatibility_score,
  personalized_roadmap, errors }`.
- **Graph nodes (sequential):**
  1. `ingest` — accept CV bytes + description, store ephemeral, emit progress.
  2. `strip` — extract clean text from CV (PDF/DOCX/TXT).
  3. `analyze` — LLM tool-call with structured schema: extract skills,
     technologies, years of experience, domain areas.
  4. `compare` — call C-RAG retriever for relevant Base Roadmap nodes
     matching extracted skills; identify gaps.
  5. `level_guess` — estimate seniority (junior/mid/senior/staff) +
     trajectory narrative; compute `compatibility_score` (0-100).
  6. `roadmap_select` — select subset of nodes addressing gaps/next steps;
     emit `personalized_roadmap`.
- **Strict-subset guardrail (ADR-008):** final node validates every selected
  `node_id` via `RoadmapIndex.is_valid_subset`. Invalid → re-plan once with a
  corrective prompt, then hard-error if still invalid. NEVER emit
  hallucinated nodes.
- **Stop criteria:** max iterations (e.g., 6), max LLM calls budget,
  structured-output validator passes.
- **Streaming:** LangGraph state events map to SSE
  `AgentProgressEvent` payloads.

---

## 10. Relational Store — Neon Postgres (C-DB)

- **Tables:**
  - `users(id UUID PK, email UNIQUE, password_hash, created_at, is_admin BOOL)`.
  - `analyses(id UUID PK, user_id FK, request JSONB, result JSONB,
    status ENUM[running,done,failed], created_at, completed_at)`.
- **Migrations:** SQL files under `docs/sql`, applied by
  `apps/ui/scripts/migrate.py` (psycopg). FastAPI uses asyncpg against the
  same schema (no second ORM).
- **Seed:** `uv run scripts/run.py seed-admin` / `seed-test`.

---

## 11. Deployment (C-DEPLOY)

- **Frontend:** `apps/ui` → Railway via `apps/ui/Dockerfile` (Streamlit).
  Env: `API_BASE_URL`, `DATABASE_URL`, `AUTHJWT_SECRET`.
- **Backend:** `apps/api` → Railway via `apps/api/Dockerfile` (uvicorn).
  Env: `QDRANT_URL`, `QDRANT_API_KEY`, `DATABASE_URL`, `LLM_API_KEY`,
  `EMBEDDING_MODEL`, `AUTHJWT_SECRET`, `CORS_ALLOW`, `BASE_ROADMAP_PATH`.
- **Qdrant:** Qdrant Cloud free cluster; collection auto-created by seeder.
- **Neon:** serverless Postgres free branch for dev + main branch for prod.
- **CI guard (optional, MVP):** on push to main → lint + tests; no auto-deploy.

---

## 12. Architectural Patterns

- **Idempotent startup seeding** (ADR-006): always run, check state, no-op if
  populated.
- **Single source of truth:** Base Roadmap JSONs are canonical; in-memory
  `RoadmapIndex` is the validator; Qdrant is the retrieval index.
- **Structured output enforcement:** LangGraph final node validates against
  the canonical index — never trusts the LLM alone.
- **No orchestration overhead:** no queues, no workers, no GPU. One process
  per service.
- **DTO synchronization:** Streamlit `ui.api.models` kept in lockstep with
  FastAPI Pydantic schemas (manual; no codegen).

---

## 13. SDD Conformance Rules (for Decomposition)

- A Task may only touch files listed here or logically subordinate to a
  declared component.
- A Task may only introduce dependencies already in the locked stack:
  Streamlit, httpx, FastAPI, Pydantic v2, LangGraph, qdrant-client,
  asyncpg / psycopg, argon2-cffi, python-jose, uv.
- No Task may add: Node/Next.js, Nx, queues (Celery/RQ), Redis, a second ORM,
  a separate worker process, or any cloud service not in §11.

---

## 14. Cross-References

- Business constraints: `.context/project_context.md`
- Locked decisions: `.context/decisions.md` (ADRs 001-008)
- Base Roadmap data: `docs/archives/*.json`
- Action plan: `.context/decomposition.json`