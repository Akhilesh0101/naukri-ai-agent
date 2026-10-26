"""Source adapter interface.

Every discovery source implements `fetch()` returning a list of RawJob. Sources
are independent and registered in the registry so new providers can be added
later without touching the ingestion pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class RawJob:
    source_key: str
    source_job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    posted_at: datetime | None = None
    posted_text: str | None = None
    experience_min: float | None = None
    experience_max: float | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)


class Source(Protocol):
    key: str
    name: str

    def fetch(self) -> list[RawJob]:
        """Return discovered jobs. Raise on transient failure to trigger retry."""
        ...

    def health_check(self) -> tuple[str, str | None]:
        """Return (status, message). status in ok|degraded|down|unknown."""
        ...
