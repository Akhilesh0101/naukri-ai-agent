"""Job ingestion: fetch from a source, dedupe, persist, score.

Handles duplicate detection (DB unique constraints + pre-check), per-source
sync history, health updates, and transient-failure retry.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.job import Job
from app.models.source import JobSource, SyncHistory
from app.services.activity_service import log_activity
from app.services.dedupe import dedupe_hash
from app.services.matching_service import score_single_job
from app.services.profile_service import get_or_create_profile
from app.sources.base import RawJob

logger = get_logger(__name__)


def _ensure_source_row(db: Session, key: str, name: str) -> JobSource:
    src = db.scalar(select(JobSource).where(JobSource.key == key))
    if src is None:
        src = JobSource(key=key, name=name, enabled=True, health="unknown")
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


def _raw_to_job(raw: RawJob) -> Job:
    now = datetime.now(timezone.utc)
    return Job(
        source_key=raw.source_key,
        source_job_id=raw.source_job_id,
        dedupe_hash=dedupe_hash(raw.title, raw.company, raw.url),
        title=raw.title,
        company=raw.company,
        location=raw.location,
        description=raw.description,
        url=raw.url,
        posted_at=raw.posted_at,
        posted_text=raw.posted_text,
        discovered_at=now,
        experience_min=raw.experience_min,
        experience_max=raw.experience_max,
        required_skills=raw.required_skills,
        preferred_skills=raw.preferred_skills,
        status="discovered",
    )


def persist_jobs(db: Session, raws: list[RawJob], score: bool = True) -> dict:
    """Insert new jobs, skipping duplicates. Returns counts. Idempotent."""
    profile = get_or_create_profile(db) if score else None
    found = len(raws)
    new = 0
    duplicate = 0

    for raw in raws:
        dh = dedupe_hash(raw.title, raw.company, raw.url)
        existing = db.scalar(
            select(Job).where(
                (Job.dedupe_hash == dh)
                | ((Job.source_key == raw.source_key) & (Job.source_job_id == raw.source_job_id))
            )
        )
        if existing is not None:
            duplicate += 1
            continue
        job = _raw_to_job(raw)
        db.add(job)
        try:
            db.flush()  # surface unique-constraint violations now
        except IntegrityError:
            db.rollback()
            duplicate += 1
            continue
        if score and profile is not None:
            score_single_job(db, job, profile, commit=False)
        new += 1

    db.commit()
    return {"jobs_found": found, "jobs_new": new, "jobs_duplicate": duplicate}


def run_sync(db: Session, source) -> dict:
    """Run one sync cycle for a source adapter. Records SyncHistory + health."""
    src_row = _ensure_source_row(db, source.key, getattr(source, "name", source.key))
    sync = SyncHistory(
        source_id=src_row.id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(sync)
    db.commit()
    db.refresh(sync)

    try:
        raws = source.fetch()
    except Exception as exc:  # transient or hard failure
        db.rollback()
        sync.status = "failed"
        sync.finished_at = datetime.now(timezone.utc)
        sync.message = f"{type(exc).__name__}: {exc}"
        src_row.health = "down"
        src_row.last_error = sync.message
        db.commit()
        log_activity(db, f"Sync failed for {source.key}: {exc}", level="error", category="sync")
        return {
            "source_key": source.key, "status": "failed",
            "jobs_found": 0, "jobs_new": 0, "jobs_duplicate": 0, "message": sync.message,
        }

    counts = persist_jobs(db, raws, score=True)

    sync.status = "success"
    sync.finished_at = datetime.now(timezone.utc)
    sync.jobs_found = counts["jobs_found"]
    sync.jobs_new = counts["jobs_new"]
    sync.jobs_duplicate = counts["jobs_duplicate"]
    sync.message = f"Found {counts['jobs_found']}, new {counts['jobs_new']}, dup {counts['jobs_duplicate']}."

    try:
        health, msg = source.health_check()
    except Exception:
        health, msg = "degraded", "health_check raised"
    src_row.health = health
    src_row.last_error = None if health == "ok" else (msg or src_row.last_error)
    src_row.last_sync_at = datetime.now(timezone.utc)
    db.commit()

    log_activity(
        db, f"Sync complete for {source.key}: {sync.message}",
        level="info", category="sync", context=counts,
    )
    return {"source_key": source.key, "status": "success", **counts, "message": sync.message}
