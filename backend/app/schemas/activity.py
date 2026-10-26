from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: str
    category: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
