"""FastAPI app factory. Modules self-register via app.core.registry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.registry import collect_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.core.events import bus

    bus.emit("app.started", {})  # modules react (e.g. pipeline recovers interrupted runs)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        description="Local-first AI content production studio. OpenAPI docs for every module.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in collect_routers():
        app.include_router(router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
