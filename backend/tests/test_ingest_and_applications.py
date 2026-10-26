"""Tests for ingestion, duplicate detection, application state machine,
idempotency, and submission-disabled behavior."""
from __future__ import annotations

from app.services.application_service import process_application
from app.services.ingest_service import persist_jobs, run_sync
from app.services.matching_service import score_single_job
from app.services.profile_service import get_or_create_profile
from app.sources.base import RawJob
from app.sources.sample import SampleSource
from app.models.job import Job
from app.models.application import Application
from sqlalchemy import select


def _raw(**kw):
    base = dict(
        source_key="test", source_job_id="J1", title="AI Engineer",
        company="Acme", location="Remote - India",
        description="Python RAG LLM FastAPI", url="https://naukri.com/j/1",
        experience_min=1, experience_max=4,
        required_skills=["Python", "RAG", "LLM"], preferred_skills=["FastAPI"],
    )
    base.update(kw)
    return RawJob(**base)


def _set_candidate_profile(db):
    profile = get_or_create_profile(db)
    profile.skills = ["Python", "RAG", "LLM", "FastAPI"]
    profile.experience_years = 2.0
    db.commit()
    return profile


def test_ingest_inserts_and_scores(db):
    _set_candidate_profile(db)
    counts = persist_jobs(db, [_raw()], score=True)
    assert counts["jobs_new"] == 1
    job = db.scalar(select(Job))
    assert job.match_result is not None
    assert job.match_score is not None


def test_duplicate_detection(db):
    _set_candidate_profile(db)
    persist_jobs(db, [_raw()], score=True)
    # Same URL again -> duplicate.
    counts = persist_jobs(db, [_raw(source_job_id="J1-again")], score=True)
    assert counts["jobs_new"] == 0
    assert counts["jobs_duplicate"] == 1


def test_sample_source_sync(db):
    _set_candidate_profile(db)
    result = run_sync(db, SampleSource())
    assert result["status"] == "success"
    assert result["jobs_new"] >= 1
    # Re-sync is idempotent (all duplicates).
    result2 = run_sync(db, SampleSource())
    assert result2["jobs_new"] == 0
    assert result2["jobs_duplicate"] == result2["jobs_found"]


def test_application_eligible_routes_to_manual(db):
    _set_candidate_profile(db)
    persist_jobs(db, [_raw()], score=True)
    job = db.scalar(select(Job))
    app_row = process_application(db, job)
    # Auto-submit disabled -> needs_attention with manual url.
    assert app_row.status == "needs_attention"
    assert app_row.manual_action_required is True
    assert app_row.confirmed is False
    assert app_row.manual_url


def test_ineligible_job_skipped(db):
    _set_candidate_profile(db)
    persist_jobs(db, [_raw(title="Principal Engineer", experience_min=12, experience_max=18)], score=True)
    job = db.scalar(select(Job))
    app_row = process_application(db, job)
    assert app_row.status == "skipped"
    assert app_row.confirmed is False


def test_application_idempotent_no_duplicate(db):
    _set_candidate_profile(db)
    persist_jobs(db, [_raw()], score=True)
    job = db.scalar(select(Job))
    a1 = process_application(db, job)
    a2 = process_application(db, job)
    assert a1.id == a2.id
    count = db.scalar(select(Application).where(Application.job_id == job.id))
    assert count is not None


def test_state_transitions_recorded(db):
    _set_candidate_profile(db)
    persist_jobs(db, [_raw()], score=True)
    job = db.scalar(select(Job))
    app_row = process_application(db, job)
    assert len(app_row.attempts) >= 1
    assert app_row.attempts[0].outcome in {"needs_attention", "submitted", "failed", "unsupported"}
