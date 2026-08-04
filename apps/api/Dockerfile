FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /bin/uv

# Build context is repo root
COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src/ ./src/
COPY docs/archives/ ./docs/archives/
COPY data/roadmaps/ ./data/roadmaps/

# Install package so `app`, `agent`, `llm`, `rag`, `roadmap` import cleanly
RUN uv pip install --system -e .

EXPOSE 8000

# Access + app logs go to container stdout/stderr (docker compose logs -f api)
# Shell-form CMD so ${PORT} is expanded at runtime (Railway injects a dynamic port)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info --access-log"]
