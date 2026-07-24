"""FastAPI application factory and lifespan."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware import RequestLoggingMiddleware
from rag.seeder import seed_roadmap_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown hooks."""
    await seed_roadmap_collection()
    yield
    # Placeholder: cleanup logic can be added here.


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dev Roadmap API",
        lifespan=lifespan,
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

    # Placeholder: include routers here when available
    # from app.routers import some_router
    # app.include_router(some_router)

    return app
