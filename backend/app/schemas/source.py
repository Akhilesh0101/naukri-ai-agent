from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    name: str
    enabled: bool
    health: str
    last_sync_at: datetime | None = None
    last_error: str | None = None


class SyncHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    jobs_found: int
    jobs_new: int
    jobs_duplicate: int
    message: str | None = None


class SyncResult(BaseModel):
    source_key: str
    status: str
    jobs_found: int
    jobs_new: int
    jobs_duplicate: int
    message: str | None = None
