"""Safe fallback provider: prepares the application and routes to manual action.

This never submits anything automatically. It records the original job link and
marks the application as needing manual action, which is the honest default
until an authorized live provider is verified.
"""
from __future__ import annotations

from typing import Any

from app.applications.base import ApplicationProvider, SubmissionResult


class ManualFallbackProvider:
    key = "manual_fallback"
    name = "Manual Fallback (no auto-submit)"
    supports_auto_submit = False

    def verify(self) -> tuple[bool, str]:
        return True, "Manual fallback is always available; it never auto-submits."

    def prepare(self, job, profile) -> dict[str, Any]:
        return {
            "job_title": job.title,
            "company": job.company,
            "job_url": job.url,
            "candidate_name": getattr(profile, "full_name", None),
            "candidate_skills": list(getattr(profile, "skills", []) or []),
            "note": "Prepared locally. Submit manually via the job link.",
        }

    def submit(self, job, profile, payload: dict[str, Any]) -> SubmissionResult:
        return SubmissionResult(
            outcome="needs_attention",
            confirmed=False,
            provider_status="manual_required",
            manual_action_required=True,
            manual_url=job.url,
            message=(
                "Automatic submission is not available for this job. The application "
                "has been prepared. Open the job link and submit manually."
            ),
            response={"prepared": True},
        )
