"""FastAPI application entry point.

Security / deployment note
--------------------------
This app is designed to run LOCALLY on 127.0.0.1 for a single user. It ships
without authentication on the assumption of localhost-only binding. Do NOT bind
to 0.0.0.0 or expose it publicly without adding authentication first (see
README "Security model"). The startup logs a warning if a non-loopback host is
configured.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.HOST not in ("127.0.0.1", "localhost", "::1"):
        logger.warning(
            "App bound to %s (not loopback). Add authentication before public exposure!",
            settings.HOST,
        )
    # Seed sources + start scheduler (best-effort; DB may be unconfigured).
    try:
        from app.db.session import SessionLocal
        from app.api.routes.sources import _seed_sources

        db = SessionLocal()
        try:
            _seed_sources(db)
        finally:
            db.close()
    except Exception as exc:  # pragma: no cover
        logger.warning("Source seeding skipped (DB not ready?): %s", exc)

    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:  # pragma: no cover
        logger.warning("Scheduler not started: %s", exc)

    yield

    try:
        from app.services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Local AI job application agent for Naukri.com (personal use).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/health",
        "auto_submit_enabled": settings.AUTO_SUBMIT_ENABLED,
    }
