"""Helper to record activity/error logs."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.activity import ActivityLog


def log_activity(
    db: Session,
    message: str,
    level: str = "info",
    category: str = "system",
    context: dict[str, Any] | None = None,
    commit: bool = True,
) -> ActivityLog:
    entry = ActivityLog(
        level=level, category=category, message=message, context=context or {}
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
