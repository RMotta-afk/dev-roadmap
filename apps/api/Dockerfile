FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /bin/uv

# Copy dependency definitions (build context is repo root)
COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src/ ./src/
COPY docs/archives/ ./docs/archives/

# Install production dependencies (uv pip ignores [tool.uv] dev-dependencies)
RUN uv pip install --system -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
