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
pnpm install:all    # Install all dependencies
pnpm infra:up       # Start Postgres + Qdrant in Docker
pnpm db:push        # Run database migrations
pnpm db:seed-admin  # Create an admin user (follow prompts)
pnpm dev            # Start frontend and backend dev servers
```

Open http://localhost:3000 and sign in with the admin credentials you just created.

## pnpm Scripts (cross-platform)

| Script | Description |
|--------|-------------|
| `pnpm install:all` | Install JS dependencies via `pnpm install` and Python dependencies via `uv sync` |
| `pnpm dev` | Run frontend (`:3000`) and backend (`:8000`) concurrently via `concurrently` |
| `pnpm dev:web` | Run only the Next.js dev server |
| `pnpm dev:api` | Run only the FastAPI dev server |
| `pnpm build` | Build the Next.js frontend for production |
| `pnpm test` | Run tests across all JS workspaces and pytest in `apps/api` |
| `pnpm lint` | Run linters across all JS workspaces and `ruff check` in `apps/api` |
| `pnpm format` | Run formatters across all JS workspaces and `ruff format` in `apps/api` |
| `pnpm infra:up` | Start local Docker services (Postgres + Qdrant) |
| `pnpm infra:down` | Stop local Docker services |
| `pnpm db:push` | Push Drizzle schema to the database |
| `pnpm db:migrate` | Run Drizzle migrations |
| `pnpm db:studio` | Open Drizzle Studio GUI |
| `pnpm db:seed-admin` | Create an admin user via CLI |

## Development Notes

- **Frontend tooling**: pnpm workspaces, Next.js 16, Tailwind v4, shadcn/ui
- **Backend tooling**: uv (Python package manager), FastAPI, LangGraph, Qdrant
- **Orchestration**: root `package.json` scripts using `concurrently` for cross-platform parallel execution
- **Requirements**: Node.js ≥ 18 + pnpm ≥ 9, Python ≥ 3.11 + uv, Docker Desktop

## Demo Setup

See [`DEMO_SETUP.md`](./DEMO_SETUP.md) for a step-by-step guide to run the app locally for a client presentation.

## Deployment

### Local Development

```bash
pnpm install:all
pnpm infra:up
pnpm db:push
pnpm db:seed-admin
pnpm dev
```

### Deploy Backend (Railway)

1. Connect your repo to Railway
2. Set the root directory to `apps/api`
3. Add environment variables from `.env.example`
4. Railway will auto-detect the `Dockerfile` and deploy

```bash
cd apps/api && docker build -t cv-analyzer-api .
docker run -p 8000:8000 --env-file .env cv-analyzer-api
```

### Deploy Frontend (Vercel)

```bash
cd apps/web && vercel --prod
```

Make sure environment variables are configured in the Vercel dashboard.

### Environment Variables Checklist

Copy `.env.local` to `.env` and fill in all values:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXTAUTH_URL` | Yes | Frontend URL for auth callbacks |
| `AUTH_SECRET` | Yes | Secret for encrypting auth tokens (NextAuth v5) |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Public API URL used by the browser |
| `QDRANT_URL` | Yes | Qdrant vector DB endpoint |
| `QDRANT_API_KEY` | No | Qdrant API key (if secured) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `LLM_API_KEY` | No | OpenAI API key (leave empty for mock mode) |
| `EMBEDDING_MODEL` | Yes | Embedding model name |
| `AUTHJS_JWT_SECRET` | Yes | JWT signing secret (must match `AUTH_SECRET`) |
| `CORS_ALLOW` | Yes | Allowed CORS origin |
| `BASE_ROADMAP_PATH` | Yes | Path to base roadmap archive files |

### Seed Admin User

```bash
pnpm db:seed-admin
```

Follow the prompts to create the first admin user. No public sign-up page exists.

## License

Private — internal use only.
