"""Sample-data source. Clearly synthetic jobs for local testing.

These are NOT real Naukri listings. They let the full pipeline be exercised
end-to-end without any live integration.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import SAMPLES_DIR
from app.sources.base import RawJob

SAMPLE_FILE = SAMPLES_DIR / "sample_jobs.json"


class SampleSource:
    key = "sample"
    name = "Sample Data (synthetic)"

    def fetch(self) -> list[RawJob]:
        if not SAMPLE_FILE.exists():
            return []
        data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
        jobs: list[RawJob] = []
        now = datetime.now(timezone.utc)
        for i, item in enumerate(data):
            posted_at = None
            hrs = item.get("posted_hours_ago")
            if hrs is not None:
                posted_at = now - timedelta(hours=float(hrs))
            jobs.append(
                RawJob(
                    source_key=self.key,
                    source_job_id=str(item.get("id", f"sample-{i}")),
                    title=item["title"],
                    company=item.get("company"),
                    location=item.get("location"),
                    description=item.get("description", ""),
                    url=item.get("url"),
                    posted_at=posted_at,
                    posted_text=item.get("posted_text"),
                    experience_min=item.get("experience_min"),
                    experience_max=item.get("experience_max"),
                    required_skills=item.get("required_skills", []),
                    preferred_skills=item.get("preferred_skills", []),
                )
            )
        return jobs

    def health_check(self) -> tuple[str, str | None]:
        if SAMPLE_FILE.exists():
            return "ok", None
        return "degraded", "sample_jobs.json not found"
