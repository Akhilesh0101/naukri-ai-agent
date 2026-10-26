"""User profile and preferences (single-user, local app)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Parsed/edited structured profile derived from the active resume.
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    structured_profile: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # ---- Preferences ----
    target_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    min_experience_years: Mapped[float] = mapped_column(Float, default=2.0)
    min_match_score: Mapped[float] = mapped_column(Float, default=75.0)

    # Weights (sum ~1.0). Configurable from the Settings page.
    weight_skills: Mapped[float] = mapped_column(Float, default=0.45)
    weight_role: Mapped[float] = mapped_column(Float, default=0.25)
    weight_experience: Mapped[float] = mapped_column(Float, default=0.20)
    weight_location: Mapped[float] = mapped_column(Float, default=0.10)

    # ---- Operational prefs ----
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_submit_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
