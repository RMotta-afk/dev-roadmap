# Deployment Task — Future Checklist

> **Status:** NOT STARTED  
> **Assigned to:** TBD  
> **Target date:** TBD

This file tracks the remaining work needed to deploy the application to production (Vercel + Railway + Qdrant Cloud + Neon Postgres).

---

## Pre-Deploy Checklist

### Environment Setup
- [ ] Copy `.env.example` → `.env.production` (do not commit)
- [ ] Set `AUTH_SECRET` to a strong random string (32+ chars)
- [ ] Set `AUTHJS_JWT_SECRET` to match `AUTH_SECRET`
- [ ] Set `LLM_API_KEY` to a real OpenAI API key (or keep empty for mock mode)
- [ ] Set `QDRANT_URL` and `QDRANT_API_KEY` from Qdrant Cloud dashboard
- [ ] Set `DATABASE_URL` from Neon Postgres dashboard
- [ ] Set `NEXT_PUBLIC_API_BASE_URL` to the Railway backend URL
- [ ] Set `NEXTAUTH_URL` to the Vercel frontend URL
- [ ] Set `CORS_ALLOW` to the Vercel frontend URL

### Backend (Railway)
- [ ] Create Railway project
- [ ] Connect GitHub repo, set root directory to `apps/api`
- [ ] Add all environment variables from `.env.production`
- [ ] Verify `Dockerfile` builds successfully
- [ ] Verify `/healthz` responds after deploy
- [ ] Verify Qdrant seeding runs on first boot (idempotent)
- [ ] Run database migrations (`pnpm db:push` or `pnpm db:migrate` against Neon)

### Frontend (Vercel)
- [ ] Create Vercel project
- [ ] Connect GitHub repo, set root directory to `apps/web`
- [ ] Add environment variables:
  - `NEXTAUTH_URL`
  - `AUTH_SECRET`
  - `NEXT_PUBLIC_API_BASE_URL`
- [ ] Verify build succeeds
- [ ] Verify `/sign-in` loads
- [ ] Verify proxy middleware redirects unauthenticated users

### Database (Neon Postgres)
- [ ] Create Neon project + branch
- [ ] Run initial migration (`pnpm db:push`)
- [ ] Create admin user (`pnpm db:seed-admin` or run CLI manually)
- [ ] Verify connection from Railway backend

### Vector Store (Qdrant Cloud)
- [ ] Create free-tier cluster
- [ ] Copy URL + API key
- [ ] Verify backend connects on boot
- [ ] Verify collection `roadmap_nodes` is created and seeded

---

## Post-Deploy Verification

- [ ] End-to-end smoke test:
  1. Sign in with admin credentials
  2. Submit a CV + description
  3. Watch streaming progress
  4. Verify results page shows Level Resume, Score, Roadmap
- [ ] Verify strict-subset guardrail (no hallucinated items)
- [ ] Verify analysis history persists to Neon
- [ ] Verify invite-only access (no public sign-up)
- [ ] Check logs on Railway for errors
- [ ] Check Vercel function logs for errors

---

## Rollback Plan

If deployment fails:
1. Railway: revert to previous deployment in dashboard
2. Vercel: revert to previous deployment in dashboard
3. Neon: branch from previous stable state if needed
4. Qdrant: re-seed from `docs/archives/*.json`

---

## Cost Estimation (MVP)

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Vercel | Hobby (free) | $0 |
| Railway | Starter | ~$5/mo |
| Neon | Free tier | $0 |
| Qdrant Cloud | Free tier (1GB) | $0 |
| OpenAI API | Pay-as-you-go | ~$0-5/mo (light usage) |
| **Total** | | **~$5/mo** |

---

## Notes

- Do **not** commit `.env` or `.env.production` to Git
- Keep `docs/archives/*.json` in the repo — they are the canonical Base Roadmap
- The Qdrant seeder is idempotent; safe to re-deploy
- Railway auto-deploys on push to `main` if configured

> Created: 2026-07-24
