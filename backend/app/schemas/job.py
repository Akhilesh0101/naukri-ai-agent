from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobIn(BaseModel):
    """Manual job entry / ingestion payload."""
    source_key: str = "manual"
    source_job_id: str | None = None
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    posted_at: datetime | None = None
    posted_text: str | None = None
    experience_min: float | None = None
    experience_max: float | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)


class MatchResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score: float
    skills_score: float
    role_score: float
    experience_score: float
    location_score: float
    semantic_score: float | None = None
    matched_skills: list[str]
    missing_skills: list[str]
    evidence: list[str]
    mandatory_failures: list[str]
    eligible: bool
    explanation: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_key: str
    source_job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    posted_at: datetime | None = None
    posted_text: str | None = None
    discovered_at: datetime | None = None
    experience_min: float | None = None
    experience_max: float | None = None
    required_skills: list[str]
    preferred_skills: list[str]
    match_score: float | None = None
    status: str
    match_result: MatchResultOut | None = None
    created_at: datetime


class UrlSearchIn(BaseModel):
    url: str
