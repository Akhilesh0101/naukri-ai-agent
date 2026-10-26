"""Profile CRUD. Single-user app: one profile row (id=1)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.profile import UserProfile


def get_or_create_profile(db: Session) -> UserProfile:
    profile = db.scalar(select(UserProfile).limit(1))
    if profile is None:
        profile = UserProfile(
            target_titles=[
                "Generative AI Engineer",
                "AI Engineer",
                "Machine Learning Engineer",
                "LLM Engineer",
                "RAG Engineer",
                "Agentic AI Engineer",
                "Python Backend Engineer",
            ],
            preferred_locations=["India", "Remote", "Hybrid"],
            min_experience_years=2.0,
            min_match_score=settings.MIN_MATCH_SCORE,
            weight_skills=settings.WEIGHT_SKILLS,
            weight_role=settings.WEIGHT_ROLE,
            weight_experience=settings.WEIGHT_EXPERIENCE,
            weight_location=settings.WEIGHT_LOCATION,
            poll_interval_minutes=settings.POLL_INTERVAL_MINUTES,
            monitoring_enabled=False,
            auto_submit_enabled=False,
            skills=[],
            structured_profile={},
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, data: dict) -> UserProfile:
    profile = get_or_create_profile(db)
    for key, value in data.items():
        if value is not None and hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
