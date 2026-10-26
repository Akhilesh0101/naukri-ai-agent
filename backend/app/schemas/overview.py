from __future__ import annotations

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_jobs: int
    matching_jobs: int
    applications_submitted_confirmed: int
    applications_prepared: int
    applications_failed: int
    needs_attention: int
    sources_healthy: int
    sources_total: int
    auto_submit_enabled: bool
    monitoring_enabled: bool
