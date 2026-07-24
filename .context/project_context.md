# Project Context: Agentic CV Analyzer & Roadmap Generator

## 1. Project Overview
A streamlined, **invite-only** application that evaluates an engineer's
professional profile by analyzing their CV and a brief self-description. An
agentic workflow extracts the user's experience, compares it against a
predefined Base Roadmap of expected engineering abilities, and outputs a
highly personalized, strictly-filtered development path alongside a profile
assessment.

- **Target users:** engineers seeking a personalized development path.
- **Access:** restricted — the site is NOT public; users are created by an
  admin (no self-signup), and all routes are auth-gated.

## 2. Architecture & Constraints
- **Repository:** monorepo. `apps/web` (Next.js), `apps/api` (FastAPI + LangGraph),
  `packages/` (shared TS types/roadmap client), `tools/`.
- **Tooling:** `pnpm` workspaces (frontend) + `Poetry`/`uv` (backend) + root
  `Makefile`. NO Nx (see ADR-001). Kept intentionally simple.
- **Languages:** Python (backend + AI workflows), TypeScript/Next.js (frontend).
- **UI constraint:** responsive-first, must work on phones and desktops.

## 3. Deployment Topology (cheap & simple — see ADRs 002-007)
| Layer        | Host                  | Notes |
|--------------|-----------------------|-------|
| Frontend     | Vercel                | Next.js App Router |
| Backend API  | Railway               | FastAPI + LangGraph, single web service |
| Vector DB    | Qdrant Cloud (free)   | 1GB managed cluster |
| Relational   | Neon Postgres (free)  | Users, sessions, analysis history |
| Roadmap data | in-repo JSON (`docs/archives/*.json`) | seeded into Qdrant at API startup |

## 4. Base Roadmap (Source of Truth)
`docs/archives/*.json` — roles: `software_engineer`, `ai_engineer`,
`frontend_engineer`; levels: junior → mid → senior → staff; nodes carry
`requirements_by_level`, `importance`, `aliases`, `content_guidance`,
`interview`.

**STRICT RULE (business constraint, see ADR-008):** the agent's
Personalized Roadmap output MUST be a pure subset of these nodes. It may only
*select and filter* — never invent, generate, or hallucinate new items.

## 5. Data Inputs (DTO)
```
{ user_name: str, phone: str, email: str,
  description: str, cv: UploadFile }
```

## 6. Outputs (DTO)
```
{ level_resume: str,
  compatibility_score: int (0-100),
  personalized_roadmap: RoadmapNode[] }   # strictly a subset of Base Roadmap
```

## 7. Frontend — apps/web (Next.js)
- App Router; Tailwind + shadcn/ui (Radix) for accessible, responsive components.
- Mobile-first responsive layout (phones + computers).
- Auth-gated routes via Auth.js middleware (NextAuth v5).
- Three product surfaces: (a) input form, (b) streaming progress / loader,
  (c) results view (Level Resume, Compatibility Score, Personalized Roadmap).

## 8. Backend — apps/api (FastAPI)
- REST + **Server-Sent Events** for streaming agent progress.
- Pydantic v2 request/response schemas; CORS allowlist.
- Verifies JWT from Auth.js; protected endpoints.
- Structured JSON logging; **self-seeds Qdrant at startup** if collection empty.

## 9. Agentic Layer (LangGraph)
Graph nodes: **ingest → strip → analyze → compare (via Qdrant retrieval) →
level-guess → roadmap-select**.
- Guardrails: structured output schema; strict-subset validator forbids
  hallucinated roadmap items (see ADR-008); max iterations + clear stop criteria.
- Tools: Qdrant retriever (role/level/category filters), roadmap validator.

## 10. RAG & Vector Store (Qdrant)
- Ingestion: parse 12 JSONs, chunk by node, embed, store with metadata
  `{role, level, node_id, category, importance}`.
- Collection design: one collection, filtered by role + level.
- Hybrid search (dense + sparse); tuned top-k for subset selection.

## 11. Auth & Access Control (Auth.js v5)
- Credentials provider: email/password (argon2) in Neon Postgres.
- JWT session cookies; middleware protects all app routes.
- Invite-only: admin creates users (no public signup route).

## 12. Non-Functional
- **Cost ceiling:** stay within all free/starter tiers for MVP.
- **Simplicity rule:** one backend service, no queues, no GPU.
- **Security:** secrets via env vars (never in repo); CV files ephemeral.
- **Observability:** structured logs; request ids.

> Authoritative architecture decisions live in `.context/decisions.md` (ADRs).