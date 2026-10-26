"""Applications and their submission attempts."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        # One active application record per job prevents duplicate submissions.
        UniqueConstraint("job_id", name="uq_application_job"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Mirrors job workflow states but tracks the application lifecycle.
    # "prepared" | "submitting" | "submitted" | "failed" | "needs_attention" | "skipped"
    status: Mapped[str] = mapped_column(String(32), default="prepared", index=True)
    provider_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed: Mapped[bool] = mapped_column(default=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_action_required: Mapped[bool] = mapped_column(default=False)
    manual_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Idempotency key to guard against double submission.
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    prepared_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    job: Mapped["Job"] = relationship(back_populates="applications")
    attempts: Mapped[list["ApplicationAttempt"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationAttempt(Base, TimestampMixin):
    __tablename__ = "application_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    # "success" | "failed" | "transient_error" | "unsupported"
    outcome: Mapped[str] = mapped_column(String(32), default="failed")
    provider_response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="attempts")
