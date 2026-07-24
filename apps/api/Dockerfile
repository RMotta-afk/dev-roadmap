FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /bin/uv

# Copy dependency definitions
COPY pyproject.toml ./
COPY src/ ./src/
COPY docs/archives/ ./docs/archives/

# Install production dependencies (no dev deps, no editable install)
RUN uv pip install --system --no-dev -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
