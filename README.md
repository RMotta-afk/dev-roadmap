# CV Analyzer & Roadmap Generator

Monorepo for an agentic CV analysis and personalized engineering roadmap generation tool.

This is a restricted-access web application that ingests an engineer's CV and brief description, runs an agentic analysis against a Base Roadmap of expected engineering abilities, and returns a personalized development path.

## Project Structure

- `apps/web` — Next.js frontend (App Router, TypeScript, Tailwind, shadcn/ui)
- `apps/api` — FastAPI + LangGraph backend (Python, uv)
- `packages/shared-types` — Shared TypeScript types and DTOs
- `packages/db` — Drizzle ORM database package

## Quick Start

```bash
make install   # Install all dependencies
make dev       # Start frontend and backend dev servers
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `help` | Print available targets |
| `install` | Install JS dependencies via `pnpm install` and Python dependencies via `uv sync` |
| `dev` | Run `pnpm --filter web dev` and `uvicorn app.main:app --reload` in parallel |
| `test` | Run `pnpm test` across workspaces and `pytest` in `apps/api` |
| `lint` | Run `pnpm lint` across workspaces and `ruff check` in `apps/api` |
| `seed` | Run the seed script for Qdrant and admin user creation |
| `format` | Run Prettier for JS/TS and `ruff format` for Python |

## Development Notes

- **Frontend tooling**: pnpm workspaces
- **Backend tooling**: uv (Python package manager)
- **Orchestration**: root Makefile for cross-ecosystem commands
- **Requirements**: Node.js + pnpm, Python 3.11+, uv

## Deployment

### Local Development

```bash
make install   # Install all dependencies
make dev       # Start frontend and backend dev servers
```

### Deploy Backend

**Docker:**
```bash
cd apps/api && docker build -t cv-analyzer-api .
docker run -p 8000:8000 --env-file .env cv-analyzer-api
```

**Railway:**
1. Connect your repo to Railway
2. Set the root directory to `apps/api`
3. Add environment variables from `.env.example`
4. Railway will auto-detect the `Dockerfile` and deploy

### Deploy Frontend

```bash
cd apps/web && vercel --prod
```

Make sure environment variables are configured in the Vercel dashboard.

### Environment Variables Checklist

Copy `.env.example` to `.env` and fill in all values:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXTAUTH_URL` | Yes | Frontend URL for auth callbacks |
| `NEXTAUTH_SECRET` | Yes | Secret for encrypting auth tokens |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Public API URL used by the browser |
| `QDRANT_URL` | Yes | Qdrant vector DB endpoint |
| `QDRANT_API_KEY` | No | Qdrant API key (if secured) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `LLM_API_KEY` | Yes | OpenAI (or compatible) API key |
| `EMBEDDING_MODEL` | Yes | Embedding model name |
| `AUTHJS_JWT_SECRET` | Yes | JWT signing secret |
| `CORS_ALLOW` | Yes | Allowed CORS origin |
| `BASE_ROADMAP_PATH` | Yes | Path to base roadmap archive files |

### Seed Admin User

```bash
pnpm --filter db create-user admin@example.com
```

## License

Private — internal use only.
