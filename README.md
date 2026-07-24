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

## License

Private — internal use only.
