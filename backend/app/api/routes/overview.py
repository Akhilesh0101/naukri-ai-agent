from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.application import Application
from app.models.job import Job
from app.models.source import JobSource
from app.schemas.overview import OverviewStats
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    matching = db.scalar(
        select(func.count(Job.id)).where(Job.match_score >= profile.min_match_score)
    ) or 0
    submitted = db.scalar(
        select(func.count(Application.id)).where(
            Application.status == "submitted", Application.confirmed.is_(True)
        )
    ) or 0
    prepared = db.scalar(
        select(func.count(Application.id)).where(Application.status == "prepared")
    ) or 0
    failed = db.scalar(
        select(func.count(Application.id)).where(Application.status == "failed")
    ) or 0
    needs = db.scalar(
        select(func.count(Application.id)).where(Application.status == "needs_attention")
    ) or 0
    sources_total = db.scalar(select(func.count(JobSource.id))) or 0
    sources_ok = db.scalar(
        select(func.count(JobSource.id)).where(JobSource.health == "ok")
    ) or 0
    return OverviewStats(
        total_jobs=total_jobs,
        matching_jobs=matching,
        applications_submitted_confirmed=submitted,
        applications_prepared=prepared,
        applications_failed=failed,
        needs_attention=needs,
        sources_healthy=sources_ok,
        sources_total=sources_total,
        auto_submit_enabled=settings.AUTO_SUBMIT_ENABLED and profile.auto_submit_enabled,
        monitoring_enabled=profile.monitoring_enabled,
    )
