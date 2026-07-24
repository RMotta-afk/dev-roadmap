# Streamlit UI

Internal invite-only UI for the CV Analyzer. Calls the FastAPI backend with a short-lived HS256 JWT after verifying credentials against Postgres.

## Local run

```bash
uv sync
uv run streamlit run src/ui/app.py
```

Requires `API_BASE_URL`, `DATABASE_URL`, and `AUTHJWT_SECRET` (see root `.env.example`).
