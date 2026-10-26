"""Activity and error logs surfaced in the dashboard."""
from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # "info" | "warning" | "error"
    level: Mapped[str] = mapped_column(String(16), default="info", index=True)
    # e.g. "sync", "match", "application", "resume", "system"
    category: Mapped[str] = mapped_column(String(32), default="system", index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
