"""Job listings and their match results."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        # Prevent duplicate jobs from the same source.
        UniqueConstraint("source_key", "source_job_id", name="uq_job_source_sourceid"),
        # Secondary dedupe key based on normalized URL / content fingerprint.
        UniqueConstraint("dedupe_hash", name="uq_job_dedupe_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    experience_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    experience_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    # "discovered" | "scored" | "eligible" | "prepared" | "submitting"
    # | "submitted" | "failed" | "needs_attention" | "skipped"
    status: Mapped[str] = mapped_column(String(32), default="discovered", index=True)

    match_result: Mapped["MatchResult | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class MatchResult(Base, TimestampMixin):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    score: Mapped[float] = mapped_column(Float, default=0.0)
    skills_score: Mapped[float] = mapped_column(Float, default=0.0)
    role_score: Mapped[float] = mapped_column(Float, default=0.0)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0)
    location_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    mandatory_failures: Mapped[list[str]] = mapped_column(JSON, default=list)
    eligible: Mapped[bool] = mapped_column(default=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    job: Mapped["Job"] = relationship(back_populates="match_result")


from app.models.application import Application  # noqa: E402  (resolve relationship)
