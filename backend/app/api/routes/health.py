from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "0.1.0"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    db_ok = True
    detail = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        db_ok = False
        detail = str(exc)
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "detail": detail,
        "auto_submit_enabled": settings.AUTO_SUBMIT_ENABLED,
    }
