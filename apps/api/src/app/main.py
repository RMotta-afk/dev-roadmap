"""FastAPI application factory and lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analyze import router as analyze_router
from app.config import settings
from app.middleware import RequestLoggingMiddleware
from llm.client import get_llm_client
from rag.seeder import seed_roadmap_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown hooks."""
    print(f"[startup] base_roadmap_path={settings.base_roadmap_path}", flush=True)

    # Auto-seed with retry (idempotent, safe for any infra)
    try:
        n = await seed_roadmap_collection(force=False)
        if n > 0:
            print(f"[startup] qdrant seed upserted={n}", flush=True)
        else:
            print("[startup] qdrant already seeded (skipped)", flush=True)
    except Exception as exc:
        print(f"[startup] qdrant seed failed (will retry): {exc}", flush=True)

    yield
    await get_llm_client().aclose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Dev Roadmap API",
        lifespan=lifespan,
    )

    secret = settings.authjwt_secret
    print(
        f"[auth] access-token secret loaded len={len(secret)} "
        f"suffix=...{secret[-4:] if len(secret) >= 4 else secret!r}",
        flush=True,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Structured JSON logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/healthz", response_class=JSONResponse)
    async def healthz():
        return {"status": "ok"}

    app.include_router(analyze_router)

    return app


# Module-level app instance for uvicorn CLI
app = create_app()
