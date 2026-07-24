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
│  ├─ web/                # Next.js (App Router, TS, Tailwind, shadcn/ui)
│  └─ api/                # FastAPI + LangGraph (Python, Poetry/uv)
├─ packages/
│  └─ shared-types/        # TS types shared with frontend (DTOs)
├─ docs/
│  ├─ archives/           # Base Roadmap JSON files (source of truth)
│  └─ sdd/                # this document
├─ .context/
│  ├─ project_context.md
│  ├─ decisions.md
│  └─ decomposition.json
├─ Makefile               # root orchestration: install/dev/test/lint/seed
├─ package.json           # pnpm workspace root
├─ pnpm-workspace.yaml
└─ .gitignore
```

**Tooling decisions (ADR-001):** pnpm workspaces for JS, Poetry/uv for Python,
root Makefile for cross-ecosystem orchestration. NO Nx.

---

## 3. Component Inventory

| ID | Component | Responsibility | SDD § |
|----|-----------|----------------|-------|
| C-FE | Frontend (apps/web) | Responsive UI, auth-gated routes, 3 product surfaces | §4 |
| C-AUTH | Auth subsystem | Auth.js credentials, JWT issuing, Neon user store, invite flow | §5 |
| C-API | Backend FastAPI | REST + SSE, Pydantic DTOs, CORS, JWT verify, logging | §6 |
| C-DATA | Base Roadmap data layer | JSON loader, Pydantic models, in-memory node index | §7 |
| C-RAG | RAG / Qdrant | Ingestion, embedding, startup seeder, hybrid retriever | §8 |
| C-AGENT | Agentic LangGraph | Graph nodes + strict-subset guardrail + structured output | §9 |
| C-DB | Relational store (Neon) | users, sessions, analysis_history tables | §10 |
| C-DEPLOY | Deployment | Dockerfile, Railway/Vercel configs, env, README | §11 |

---

## 4. Frontend (C-FE)

- **Stack:** Next.js App Router, TypeScript strict, Tailwind CSS, shadcn/ui
  (Radix primitives). Auth.js v5 for auth.
- **Routing groups:**
  - `/sign-in` — public sign-in page (no signup).
  - `(app)/` — protected group (Auth.js middleware); contains:
    - `/` → `analyze` surface (input form).
    - `/analyze/:id` → `progress` surface (SSE stream) and `results` surface.
- **Responsive shell:** `<Header/>`, `<Nav/>` (mobile drawer), `<Main/>`.
  Breakpoints; mobile-first.
- **Design system tokens:** color, spacing, typography defined via Tailwind
  theme + shadcn primitives.
- **API integration:** typed fetcher hitting FastAPI `/analyze` SSE endpoint;
  DTOs synchronized from `packages/shared-types`.

---

## 5. Auth Subsystem (C-AUTH)

- **Provider:** Auth.js v5 credentials provider.
- **Password hashing:** argon2.
- **Session:** JWT in HttpOnly cookies; short-lived access + refresh.
- **Public routes:** only `/sign-in`. No self-signup.
- **Invite flow:** admin creates users via a CLI/script backed by Neon
  Postgres (admin token readable from env; no admin UI required for MVP).
- **Backend verification (C-API):** FastAPI dependency decodes & verifies the
  Auth.js JWT (shared secret / JWKS), attaching `user_id` to the request
  state. Protected endpoints reject unauthenticated requests with 401.

---

## 6. Backend FastAPI (C-API)

- **App factory:** `create_app()` producing the FastAPI instance.
- **Middleware:** CORS allowlist (Vercel domain + localhost), structured JSON
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
  Auth.js secret, embedding model, LLM provider/key).
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
  - Optional `sessions` only if Auth.js uses DB sessions (MVP uses JWT, so
    no sessions table).
- **Migrations:** one migration framework — Drizzle ORM (TS, for frontend
  / Auth.js) — or a shared SQL migration directory. Decision: use Drizzle in
  `packages/db` so both the Auth.js side and any admin tooling share one
  schema definition. The FastAPI side uses asyncpg + reflects the same schema
  via Pydantic models (no second ORM).
- **Seed:** an admin user + restricted test users via a guarded `make seed-admin`
  with env-supplied credentials.

---

## 11. Deployment (C-DEPLOY)

- **Frontend:** `apps/web` → Vercel (auto-detect Next.js). Env vars:
  `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `AUTHJS_JWKS_URL` / shared secret,
  `NEXT_PUBLIC_API_BASE_URL`.
- **Backend:** `apps/api` → Railway via `Dockerfile` (slim Python base, uv
  install, `uvicorn` entrypoint). Env vars: `QDRANT_URL`, `QDRANT_API_KEY`,
  `DATABASE_URL`, `LLM_API_KEY`, `EMBEDDING_MODEL`, `AUTHJS_JWT_SECRET`,
  `CORS_ALLOW`, `BASE_ROADMAP_PATH`.
- **Qdrant:** Qdrant Cloud free cluster; collection auto-created by seeder.
- **Neon:** serverless Postgres free branch for dev + main branch for prod.
- **CI guard (optional, MVP):** on push to main → lint + typecheck + tests;
  no auto-deploy.

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
- **DTO synchronization:** `packages/shared-types` is generated/edited in
  lockstep with the FastAPI Pydantic schemas (manual keep-in-sync for MVP;
  no codegen pipeline required).

---

## 13. SDD Conformance Rules (for Decomposition)

- A Task may only touch files listed here or logically subordinate to a
  declared component.
- A Task may only introduce dependencies already in the locked stack
  (ADR-007): Next.js, Tailwind, shadcn/ui, Auth.js v5, FastAPI, Pydantic v2,
  LangGraph, qdrant-client, asyncpg / Drizzle, Poetry/uv, pnpm.
- No Task may add: Nx, queues (Celery/RQ), Redis, a second ORM, a frontend
  state library beyond what Next.js + fetch provide for MVP, a separate
  worker process, or any cloud service not in §11.

---

## 14. Cross-References

- Business constraints: `.context/project_context.md`
- Locked decisions: `.context/decisions.md` (ADRs 001-008)
- Base Roadmap data: `docs/archives/*.json`
- Action plan: `.context/decomposition.json`