"""Multi-step job-processing pipeline.

This mirrors a LangGraph node graph (discover -> score -> check eligibility ->
prepare/apply) but is implemented with plain Python so it runs with zero extra
heavy dependencies. Each step is a pure-ish function over a small state dict,
which makes it trivial to port to LangGraph later if desired:

    discover -> score -> eligibility_gate -> apply_or_skip

To use LangGraph instead, wrap each `step_*` function as a node and connect
them with edges; the state contract is unchanged.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.job import Job
from app.services.application_service import process_application
from app.services.matching_service import score_single_job
from app.services.profile_service import get_or_create_profile

logger = get_logger(__name__)


def step_score(db: Session, job: Job, state: dict[str, Any]) -> dict[str, Any]:
    profile = state["profile"]
    mr = score_single_job(db, job, profile, commit=True)
    state["score"] = mr.score
    state["eligible"] = mr.eligible
    state["mandatory_failures"] = mr.mandatory_failures
    return state


def step_eligibility_gate(job: Job, state: dict[str, Any]) -> dict[str, Any]:
    state["proceed"] = bool(state.get("eligible"))
    return state


def step_apply_or_skip(db: Session, job: Job, state: dict[str, Any]) -> dict[str, Any]:
    if state.get("proceed"):
        app_row = process_application(db, job)
        state["application_status"] = app_row.status
    else:
        job.status = "skipped"
        db.commit()
        state["application_status"] = "skipped"
    return state


def process_job(db: Session, job: Job, profile=None) -> dict[str, Any]:
    """Run the full pipeline for a single job."""
    profile = profile or get_or_create_profile(db)
    state: dict[str, Any] = {"profile": profile, "job_id": job.id}
    state = step_score(db, job, state)
    state = step_eligibility_gate(job, state)
    state = step_apply_or_skip(db, job, state)
    # Do not leak ORM objects in the returned state.
    return {k: v for k, v in state.items() if k != "profile"}


def process_eligible_jobs(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """Process all currently eligible jobs that have no application yet."""
    profile = get_or_create_profile(db)
    jobs = db.scalars(
        select(Job).where(Job.status == "eligible").limit(limit)
    ).all()
    results = []
    for job in jobs:
        results.append(process_job(db, job, profile))
    return results
