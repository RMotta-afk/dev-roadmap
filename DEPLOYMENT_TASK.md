# Deployment Task — Streamlit + FastAPI

> **Status:** NOT STARTED  
> **Stack:** Railway (api + ui) · Neon Postgres · Qdrant Cloud  
> **Removed:** Vercel / Next.js / Node

---

## Pre-Deploy Checklist

### Environment

- [ ] Copy `.env.example` → production secrets (do not commit)
- [ ] Set `AUTHJWT_SECRET` to a strong random string (32+ chars) — **same value on api and ui**
- [ ] Set `LLM_API_KEY` (or leave empty for mock mode)
- [ ] Set `QDRANT_URL` and `QDRANT_API_KEY` from Qdrant Cloud
- [ ] Set `DATABASE_URL` from Neon (api may use `postgresql+asyncpg://…`)
- [ ] Set UI `API_BASE_URL` to the Railway API public or private URL
- [ ] Set `CORS_ALLOW` if any browser client calls the API (optional when UI uses server-side httpx only)
- [ ] Set `BASE_ROADMAP_PATH=docs/archives` on api

### Database (Neon)

- [ ] Create Neon project + branch
- [ ] Run `uv run python apps/ui/scripts/migrate.py` against Neon (`DATABASE_URL` without requiring Node)
- [ ] Create admin: `uv run python apps/ui/scripts/create_user.py you@company.com '…' --admin`
- [ ] Verify api and ui can connect

### Vector store (Qdrant Cloud)

- [ ] Create free-tier cluster
- [ ] Copy URL + API key onto api service
- [ ] Confirm collection `roadmap_nodes` seeds on first api boot

### Backend (Railway — api)

- [ ] Create Railway project / service
- [ ] Root / Dockerfile: repo root context, `apps/api/Dockerfile`
- [ ] Env vars from checklist above
- [ ] Verify `GET /healthz` → `{"status":"ok"}`
- [ ] Confirm Qdrant seed logs on first boot

### Frontend (Railway — ui)

- [ ] Second Railway service from same repo
- [ ] Dockerfile: `apps/ui/Dockerfile` (build context = repo root)
- [ ] Env: `API_BASE_URL`, `DATABASE_URL`, `AUTHJWT_SECRET` (match api)
- [ ] Prefer Railway private networking URL for `API_BASE_URL` when both services share a project
- [ ] Open public UI URL; confirm sign-in page loads
- [ ] Port: Streamlit listens on `$PORT` if Railway injects it — override CMD if needed:

```dockerfile
CMD streamlit run src/ui/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
```

---

## Post-Deploy Verification

- [ ] Sign in with admin credentials
- [ ] Submit CV + description
- [ ] Watch streaming progress steps
- [ ] Results show level resume, score, roadmap
- [ ] Invite-only: no public signup
- [ ] Check Railway logs on api and ui

---

## Rollback

1. Railway: redeploy previous successful deployment per service  
2. Neon: restore branch / PITR if schema broken  
3. Qdrant: re-seed from `docs/archives/*.json` via api restart  

---

## Local Docker parity

```bash
docker compose up --build
# UI http://localhost:8501  API http://localhost:8000/healthz
```
