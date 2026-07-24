# Project Decisions Log

This file records the key technical and architectural decisions made for the
**Agentic CV Analyzer & Roadmap Generator** project, along with their rationale.
It serves as the authoritative reference for why the project is structured the
way it is. New decisions should be appended (never rewritten) so the history is
preserved.

---

## ADR-001 — Monorepo without Nx

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** The project must be a monorepo with a Python backend and a
  Next.js frontend. Nx was considered because it offers unified task graphs,
  caching and codegen for polyglot monorepos.
- **Decision:** Use a **plain uv monorepo** instead of Nx (later: pure Python;
  see ADR-009).
  - Originally: `pnpm` + `uv` + Makefile.
  - Now: `uv` for API and UI; `scripts/run.py` orchestrates install/dev/seed.
- **Rationale:** Matches the project's "simplest possible" constraint. Nx's
  Python support relies on a third-party plugin (`@nxlv/python`), adding
  cognitive/operational overhead for a small project. A plain workspace + Make
  targets deliver ~90% of orchestration value at a fraction of the complexity.
- **Revisit trigger:** If the monorepo grows beyond ~4 apps/packages or the
  team exceeds 2 contributors.

---

## ADR-002 — Backend hosting on Railway

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** The frontend deploys cleanly to Vercel. The backend hosts a
  FastAPI service plus a LangGraph agentic layer with potentially long-running
  agent loops. Candidate hosts: Railway, Render, Fly.io, Vercel Python
  functions.
- **Decision:** Deploy the **FastAPI + LangGraph backend as a single web
  service on Railway**. The Next.js frontend deploys to Vercel.
- **Rationale:** LangGraph agents are long-running, which is incompatible with
  Vercel serverless function time limits (10s hobby / 60s pro). Railway offers
  one-Procfile/Dockerfile deploy, a generous free starter credit, and no
  infra management — the cheapest "simple" option that supports persistent
  processes.
- **Alternatives rejected:**
  - Render: comparable DX; Railway chosen for marginally simpler DX.
  - Fly.io: more config surface (`fly.toml`, regions).
  - Vercel functions: incompatible with long-running agents.
- **Revisit trigger:** Cost exceeds free/starter tier or need for GPU.

---

## ADR-003 — Qdrant Cloud (free tier) as the vector store

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** RAG over the Base Roadmap (~12 JSON files) requires a vector
  store. Options: Qdrant Cloud, self-hosted Qdrant (Docker), Qdrant embedded
  (in-process).
- **Decision:** Use **Qdrant Cloud free tier** (1GB managed cluster).
- **Rationale:** The Base Roadmap dataset is small (a few hundred nodes), well
  within the 1GB free quota. Managed Qdrant removes self-hosting ops burden
  and pairs well with the single backend service on Railway.
- **Revisit trigger:** Dataset grows past 1GB or need for on-prem latency
  guarantees.

---

## ADR-004 — Auth.js v5 (NextAuth) with credentials provider

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** Access must be restricted (invite-only). Options: Auth.js v5
  credentials, Clerk (managed), Supabase Auth, static invite code.
- **Decision:** Use **Auth.js v5** with a **JWT credentials provider** —
  email + password stored in Postgres, hashed with argon2. JWT session cookies
  are issued; the FastAPI backend verifies the JWT on protected routes.
- **Rationale:** Open-source, no vendor lock-in, full control over the
  invite-only flow (no public signup route; an admin creates users). Keeps the
  auth model simple and portable.
- **Revisit trigger:** If sign-in/social-login becomes a priority, swap the
  provider without changing the backend JWT-verification contract.

---

## ADR-005 — Neon Postgres (free tier) for relational data

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** The app needs persistent storage for users, sessions and
  analysis history. Options: Neon Postgres, Supabase Postgres, SQLite on the
  host.
- **Decision:** Use **Neon Postgres free tier** (0.5GB serverless Postgres with
  branching).
- **Rationale:** Serverless Postgres with sensible free quota; clean pairing
  with Auth.js credentials; no infra to manage. Branching supports dev/preview
  environments.
- **Revisit trigger:** Data exceeds 0.5GB or need for multi-region writes.

---

## ADR-006 — App-seeded Qdrant at startup

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** The Base Roadmap lives as 12 JSON files in `docs/archives/`.
  Those must reach Qdrant. Options: seed at API startup, standalone seed
  script, CI-driven re-index.
- **Decision:** The **FastAPI app self-seeds Qdrant on startup** if the
  collection is empty: read the JSONs, chunk by node, embed, upsert with
  metadata. The check is idempotent.
- **Rationale:** Simplest, no separate job or CI step; ensures the vector
  store and the versioned roadmap data can never drift on a fresh deploy.
  Idempotency keeps re-deploys safe.
- **Revisit trigger:** If incremental sync or frequent roadmap edits make a
  re-index costly, move to a CI-driven re-index on `docs/archives/**` changes.

---

## ADR-007 — Tech stack summary (historical lock; superseded for FE by ADR-009)

| Concern              | Choice                                      |
|-----------------------|---------------------------------------------|
| Monorepo tooling      | uv + scripts/run.py (was pnpm/Make)         |
| Frontend              | Streamlit (was Next.js) — see ADR-009       |
| Backend framework     | FastAPI (async, Pydantic v2)                |
| Agentic layer         | LangGraph                                    |
| Vector store          | Qdrant Cloud (free)                         |
| Relational store      | Neon Postgres (free)                        |
| Auth                  | Streamlit login + HS256 JWT (ADR-009)       |
| Frontend hosting      | Railway                                      |
| Backend hosting       | Railway                                      |
| Base Roadmap source   | `docs/archives/*.json` (versioned in repo)  |

## ADR-008 — Strict-subset output contract (business rule)

- **Date:** 2026-07-24
- **Status:** Accepted (carried from the original project context)
- **Context:** The Personalized Roadmap must be a pure subset of the Base
  Roadmap. The agent is forbidden from inventing new skills/modules/steps.
- **Decision:** Enforce this as a **structured-output guardrail** in the
  LangGraph final node: the validator rejects any roadmap item whose `id` is
  not present in the loaded Base Roadmap. The agent re-plans or emits a
  validation error rather than returning hallucinated items.
  - **Rationale:** Hard-codes the project's core business constraint at the
  graph layer, not just the prompt.

---

## ADR-009 — Replace Next.js with Streamlit (internal-use UI)

- **Date:** 2026-07-24
- **Status:** Accepted
- **Context:** Product is simple and internal. Maintaining Next.js + Auth.js +
  pnpm + Vercel added polyglot complexity while the backend is fully Python.
- **Decision:**
  - Remove `apps/web`, `packages/*`, and all Node/pnpm tooling.
  - Add `apps/ui` Streamlit client that talks to FastAPI with server-side
    httpx and mints HS256 JWTs after argon2 login against Postgres.
  - Host both UI and API on Railway; keep Neon + Qdrant Cloud.
  - Own schema SQL under `docs/sql` with Python migrate/seed scripts.
- **Rationale:** One language, simpler local/dev ops, same analysis contracts.
- **Revisit trigger:** Multi-tenant public product or heavy client-side UX.