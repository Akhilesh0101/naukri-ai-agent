from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    full_name: str | None = None
    email: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    structured_profile: dict[str, Any] = Field(default_factory=dict)
    target_titles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    min_experience_years: float = 2.0
    min_match_score: float = 75.0
    weight_skills: float = 0.45
    weight_role: float = 0.25
    weight_experience: float = 0.20
    weight_location: float = 0.10
    poll_interval_minutes: int = 30
    monitoring_enabled: bool = False
    auto_submit_enabled: bool = False
    notify_email: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    skills: list[str] | None = None
    experience_years: float | None = None
    structured_profile: dict[str, Any] | None = None
    target_titles: list[str] | None = None
    preferred_locations: list[str] | None = None
    min_experience_years: float | None = None
    min_match_score: float | None = None
    weight_skills: float | None = None
    weight_role: float | None = None
    weight_experience: float | None = None
    weight_location: float | None = None
    poll_interval_minutes: int | None = None
    monitoring_enabled: bool | None = None
    auto_submit_enabled: bool | None = None
    notify_email: str | None = None


class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
