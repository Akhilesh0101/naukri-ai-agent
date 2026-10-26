from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str | None = None
    size_bytes: int
    parsed: dict[str, Any]
    is_active: bool
    created_at: datetime


class ResumeParsed(BaseModel):
    skills: list[str]
    experience_years: float | None
    education: list[str]
    projects: list[str]
    technologies: list[str]
    accomplishments: list[str]
    raw_text_chars: int
