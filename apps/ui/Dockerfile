FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /bin/uv

COPY apps/ui/pyproject.toml apps/ui/README.md ./
COPY apps/ui/src/ ./src/
COPY apps/ui/.streamlit/ ./.streamlit/

RUN uv pip install --system -e .

EXPOSE 8501

ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["sh", "-c", "streamlit run src/ui/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
