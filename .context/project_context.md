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
  admin (no self-signup), and all surfaces are auth-gated.

## 2. Architecture & Constraints
- **Repository:** monorepo. `apps/ui` (Streamlit), `apps/api` (FastAPI + LangGraph).
- **Tooling:** `uv` for both apps + `scripts/run.py`. NO Node/pnpm/Make/Nx.
- **Languages:** Python only (UI + backend + AI workflows).
- **UI constraint:** simple internal Streamlit UI (form, progress, results).

## 3. Deployment Topology (cheap & simple)
| Layer        | Host                  | Notes |
|--------------|-----------------------|-------|
| Frontend     | Railway               | Streamlit (`apps/ui`) |
| Backend API  | Railway               | FastAPI + LangGraph |
| Vector DB    | Qdrant Cloud (free)   | 1GB managed cluster |
| Relational   | Neon Postgres (free)  | Users, analysis history |
| Roadmap data | in-repo JSON (`docs/archives/*.json`) | seeded into Qdrant at API startup |

## 4. Base Roadmap (Source of Truth)
`docs/archives/*.json` — roles/levels and nodes with requirements, importance,
aliases, content guidance.

**STRICT RULE (ADR-008):** Personalized Roadmap MUST be a pure subset of these
nodes — select/filter only, never invent.

## 5. Data Inputs (DTO)
```
{ user_name: str, phone: str, email: str,
  description: str, cv: UploadFile }
```

## 6. Outputs (DTO)
```
{ level_resume | level_estimate,
  compatibility_score: int (0-100),
  personalized_roadmap: RoadmapNode[] }
```

## 7. Frontend — apps/ui (Streamlit)
- Sign-in, analyze form, SSE progress, results.
- Server-side httpx + JWT mint to FastAPI.
- Session state after argon2 login against Postgres.

## 8. Backend — apps/api (FastAPI)
- REST + SSE for streaming agent progress.
- Pydantic v2; CORS allowlist; JWT Bearer verify (`AUTHJWT_SECRET`).
- Structured JSON logging; self-seeds Qdrant at startup if empty.

## 9. Agentic Layer (LangGraph)
Graph: **ingest → strip → analyze → compare → level-guess → roadmap-select**.
Strict-subset validator on final roadmap (ADR-008).

## 10. RAG & Vector Store (Qdrant)
Parse archives, embed nodes, hybrid retrieve with filters.

## 11. Auth & Access Control
- Streamlit credentials against Neon/Postgres users (argon2).
- Short-lived HS256 JWT for API (`sub`, `email`, `is_admin`).
- Invite-only: CLI create_user / seed_test_user (no public signup).

## 12. Non-Functional
- Cost: free/starter tiers for MVP.
- One backend process, no queues, no GPU.
- Secrets via env; CV files ephemeral.
- Structured logs.

> ADRs: `.context/decisions.md`
