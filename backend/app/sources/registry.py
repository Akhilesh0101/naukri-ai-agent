"""Registry of available discovery sources (excluding on-demand URL search)."""
from __future__ import annotations

from app.sources.base import Source
from app.sources.email_alert import EmailAlertSource
from app.sources.sample import SampleSource


def build_sources() -> dict[str, Source]:
    sources: list[Source] = [SampleSource(), EmailAlertSource()]
    return {s.key: s for s in sources}


# Static metadata for seeding the job_sources table.
SOURCE_METADATA = [
    {"key": "sample", "name": "Sample Data (synthetic)", "enabled": True},
    {"key": "email_alert", "name": "Email Job Alerts (authorized export)", "enabled": False},
    {"key": "manual", "name": "Manual Entry", "enabled": True},
    {"key": "url_search", "name": "Naukri URL Search (authorized fetch)", "enabled": True},
]
