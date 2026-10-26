"""Application workflow state machine and safeguards.

States: discovered -> scored -> eligible -> prepared -> submitting ->
submitted | failed | needs_attention | skipped

Safeguards:
  - eligibility + mandatory rules enforced before preparing
  - duplicate submission prevented (unique job_id + idempotency key)
  - auto-submit gated behind AUTO_SUBMIT_ENABLED and a verified provider
  - never reports success without reliable confirmation
  - never invents screening answers or false qualifications
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.registry import get_provider
from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.application import Application, ApplicationAttempt
from app.models.job import Job
from app.services.activity_service import log_activity
from app.services.profile_service import get_or_create_profile

logger = get_logger(__name__)

VALID_JOB_STATES = {
    "discovered", "scored", "eligible", "prepared", "submitting",
    "submitted", "failed", "needs_attention", "skipped",
}


class ApplicationError(Exception):
    pass


def _idempotency_key(job: Job) -> str:
    basis = f"{job.id}:{job.source_key}:{job.source_job_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:48]


def get_application_for_job(db: Session, job_id: int) -> Application | None:
    return db.scalar(select(Application).where(Application.job_id == job_id))


def process_application(db: Session, job: Job, *, force: bool = False) -> Application:
    """Run the application workflow for a single job.

    Honors eligibility, prevents duplicates, and respects the auto-submit gate.
    Returns the Application row (prepared or submitted/needs_attention).
    """
    profile = get_or_create_profile(db)

    # ---- Eligibility / mandatory checks ----
    mr = job.match_result
    if mr is None:
        raise ApplicationError("Job has not been scored yet.")
    if not force and not mr.eligible:
        reasons = mr.mandatory_failures or ["Below match threshold."]
        job.status = "skipped"
        db.commit()
        log_activity(
            db, f"Skipped job {job.id} ({job.title}): not eligible.",
            level="info", category="application",
            context={"reasons": reasons, "score": mr.score},
        )
        app_row = get_application_for_job(db, job.id)
        if app_row is None:
            app_row = Application(
                job_id=job.id, status="skipped",
                idempotency_key=_idempotency_key(job),
                failure_reason="; ".join(reasons),
            )
            db.add(app_row)
            db.commit()
            db.refresh(app_row)
        return app_row

    # ---- Duplicate guard ----
    existing = get_application_for_job(db, job.id)
    if existing is not None and existing.status in ("submitted", "submitting", "prepared", "needs_attention"):
        log_activity(
            db, f"Application already exists for job {job.id} (status={existing.status}).",
            level="info", category="application",
        )
        return existing

    provider_key = None  # default -> manual fallback unless auto-submit is on
    auto = settings.AUTO_SUBMIT_ENABLED and profile.auto_submit_enabled
    provider = get_provider(provider_key)

    # ---- Prepare ----
    payload = provider.prepare(job, profile)
    app_row = existing or Application(
        job_id=job.id, idempotency_key=_idempotency_key(job)
    )
    app_row.status = "prepared"
    app_row.provider_key = provider.key
    app_row.prepared_payload = payload
    if existing is None:
        db.add(app_row)
    job.status = "prepared"
    db.commit()
    db.refresh(app_row)
    log_activity(db, f"Prepared application for job {job.id} ({job.title}).",
                 level="info", category="application")

    # ---- Submit (only if auto-submit is enabled AND provider supports it) ----
    if not auto or not provider.supports_auto_submit:
        # Safe fallback path -> needs_attention.
        result = provider.submit(job, profile, payload)
        _record_attempt(db, app_row, result)
        app_row.status = "needs_attention" if result.manual_action_required else result.outcome
        app_row.provider_status = result.provider_status
        app_row.manual_action_required = result.manual_action_required
        app_row.manual_url = result.manual_url or job.url
        app_row.failure_reason = None if result.confirmed else result.message
        job.status = "needs_attention"
        db.commit()
        db.refresh(app_row)
        reason = "auto-submit disabled" if not auto else "provider has no verified auto-submit"
        log_activity(
            db, f"Job {job.id} routed to manual action ({reason}).",
            level="warning", category="application",
            context={"manual_url": app_row.manual_url},
        )
        return app_row

    # ---- Verified auto-submit path ----
    ok, msg = provider.verify()
    if not ok:
        app_row.status = "needs_attention"
        app_row.manual_action_required = True
        app_row.manual_url = job.url
        app_row.failure_reason = f"Provider not verified: {msg}"
        job.status = "needs_attention"
        db.commit()
        db.refresh(app_row)
        return app_row

    app_row.status = "submitting"
    job.status = "submitting"
    db.commit()

    result = provider.submit(job, profile, payload)
    _record_attempt(db, app_row, result)

    if result.outcome == "submitted" and result.confirmed:
        app_row.status = "submitted"
        app_row.confirmed = True
        app_row.submitted_at = datetime.now(timezone.utc)
        app_row.provider_status = result.provider_status
        app_row.provider_reference = result.provider_reference
        job.status = "submitted"
    elif result.outcome == "transient_error":
        app_row.status = "failed"
        app_row.failure_reason = result.message
        job.status = "failed"
    else:
        app_row.status = "needs_attention"
        app_row.manual_action_required = True
        app_row.manual_url = result.manual_url or job.url
        app_row.failure_reason = result.message
        job.status = "needs_attention"

    db.commit()
    db.refresh(app_row)
    return app_row


def _record_attempt(db: Session, app_row: Application, result) -> None:
    count = len(app_row.attempts) + 1
    attempt = ApplicationAttempt(
        application_id=app_row.id,
        attempt_number=count,
        outcome=result.outcome,
        provider_response=result.response or {},
        message=result.message,
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
