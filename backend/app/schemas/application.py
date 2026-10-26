from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    attempt_number: int
    outcome: str
    message: str | None = None
    attempted_at: datetime | None = None
    created_at: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    status: str
    provider_key: str | None = None
    provider_status: str | None = None
    provider_reference: str | None = None
    submitted_at: datetime | None = None
    confirmed: bool
    failure_reason: str | None = None
    manual_action_required: bool
    manual_url: str | None = None
    created_at: datetime
    attempts: list[ApplicationAttemptOut] = []
