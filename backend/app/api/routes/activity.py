from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.activity import ActivityLog
from app.schemas.activity import ActivityLogOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityLogOut])
def list_activity(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
    level: str | None = None,
    category: str | None = None,
):
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc())
    if level:
        stmt = stmt.where(ActivityLog.level == level)
    if category:
        stmt = stmt.where(ActivityLog.category == category)
    return list(db.scalars(stmt.limit(limit)))
