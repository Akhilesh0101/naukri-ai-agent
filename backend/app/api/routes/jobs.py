from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.job import Job
from app.schemas.common import Page
from app.schemas.job import JobIn, JobOut
from app.services.dedupe import dedupe_hash
from app.services.matching_service import score_single_job
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=Page[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    min_score: float | None = None,
    company: str | None = None,
    location: str | None = None,
    q: str | None = None,
    sort: str = Query("score", pattern="^(score|posted|discovered)$"),
):
    stmt = select(Job).options(selectinload(Job.match_result))
    count_stmt = select(func.count(Job.id))
    if status:
        stmt = stmt.where(Job.status == status)
        count_stmt = count_stmt.where(Job.status == status)
    if min_score is not None:
        stmt = stmt.where(Job.match_score >= min_score)
        count_stmt = count_stmt.where(Job.match_score >= min_score)
    if company:
        stmt = stmt.where(Job.company.ilike(f"%{company}%"))
        count_stmt = count_stmt.where(Job.company.ilike(f"%{company}%"))
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
        count_stmt = count_stmt.where(Job.location.ilike(f"%{location}%"))
    if q:
        stmt = stmt.where(Job.title.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(Job.title.ilike(f"%{q}%"))

    if sort == "score":
        stmt = stmt.order_by(Job.match_score.desc().nullslast())
    elif sort == "posted":
        stmt = stmt.order_by(Job.posted_at.desc().nullslast())
    else:
        stmt = stmt.order_by(Job.discovered_at.desc().nullslast())

    total = db.scalar(count_stmt) or 0
    items = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.scalar(
        select(Job).options(selectinload(Job.match_result)).where(Job.id == job_id)
    )
    if job is None:
        raise HTTPException(404, "Job not found.")
    return job


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobIn, db: Session = Depends(get_db)):
    """Manual job entry. Deduplicated and scored immediately."""
    dh = dedupe_hash(payload.title, payload.company, payload.url)
    source_job_id = payload.source_job_id or dh[:16]
    existing = db.scalar(select(Job).where(Job.dedupe_hash == dh))
    if existing is not None:
        raise HTTPException(409, f"Duplicate job (already exists as id {existing.id}).")

    job = Job(
        source_key=payload.source_key,
        source_job_id=source_job_id,
        dedupe_hash=dh,
        title=payload.title,
        company=payload.company,
        location=payload.location,
        description=payload.description,
        url=payload.url,
        posted_at=payload.posted_at,
        posted_text=payload.posted_text,
        discovered_at=datetime.now(timezone.utc),
        experience_min=payload.experience_min,
        experience_max=payload.experience_max,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        status="discovered",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    profile = get_or_create_profile(db)
    score_single_job(db, job, profile)
    db.refresh(job)
    return job


@router.post("/{job_id}/score", response_model=JobOut)
def rescore_job(job_id: int, db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id))
    if job is None:
        raise HTTPException(404, "Job not found.")
    profile = get_or_create_profile(db)
    score_single_job(db, job, profile)
    db.refresh(job)
    return job
