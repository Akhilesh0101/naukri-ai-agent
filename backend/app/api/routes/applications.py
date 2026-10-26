from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.applications.registry import list_providers
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import ApplicationOut
from app.schemas.common import Page
from app.services.application_service import ApplicationError, process_application

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=Page[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    stmt = select(Application).options(selectinload(Application.attempts))
    count_stmt = select(func.count(Application.id))
    if status:
        stmt = stmt.where(Application.status == status)
        count_stmt = count_stmt.where(Application.status == status)
    stmt = stmt.order_by(Application.created_at.desc())
    total = db.scalar(count_stmt) or 0
    items = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/job/{job_id}", response_model=ApplicationOut)
def apply_to_job(job_id: int, force: bool = False, db: Session = Depends(get_db)):
    job = db.scalar(
        select(Job).options(selectinload(Job.match_result)).where(Job.id == job_id)
    )
    if job is None:
        raise HTTPException(404, "Job not found.")
    try:
        app_row = process_application(db, job, force=force)
    except ApplicationError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.refresh(app_row)
    return app_row


@router.post("/{application_id}/retry", response_model=ApplicationOut)
def retry_application(application_id: int, db: Session = Depends(get_db)):
    app_row = db.scalar(select(Application).where(Application.id == application_id))
    if app_row is None:
        raise HTTPException(404, "Application not found.")
    if app_row.status not in ("failed", "needs_attention"):
        raise HTTPException(400, f"Cannot retry an application in status '{app_row.status}'.")
    job = db.scalar(
        select(Job).options(selectinload(Job.match_result)).where(Job.id == app_row.job_id)
    )
    try:
        app_row = process_application(db, job, force=False)
    except ApplicationError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.refresh(app_row)
    return app_row


@router.get("/providers")
def providers():
    return list_providers()
