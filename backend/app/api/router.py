"""Aggregate all API routers under /api."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    activity,
    applications,
    health,
    jobs,
    monitoring,
    overview,
    profile,
    resume,
    search,
    semantic,
    sources,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(overview.router)
api_router.include_router(profile.router)
api_router.include_router(resume.router)
api_router.include_router(jobs.router)
api_router.include_router(sources.router)
api_router.include_router(search.router)
api_router.include_router(applications.router)
api_router.include_router(activity.router)
api_router.include_router(monitoring.router)
api_router.include_router(semantic.router)
