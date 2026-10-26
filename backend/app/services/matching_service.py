"""Score jobs against the active profile and persist MatchResult rows."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.matching.scorer import (
    CandidateProfile,
    JobPosting,
    Weights,
    score_job,
)
from app.models.job import Job, MatchResult
from app.models.profile import UserProfile


def _candidate_from_profile(profile: UserProfile) -> CandidateProfile:
    raw_text = ""
    if isinstance(profile.structured_profile, dict):
        raw_text = profile.structured_profile.get("raw_text", "") or ""
    return CandidateProfile(
        skills=list(profile.skills or []),
        experience_years=profile.experience_years,
        target_titles=list(profile.target_titles or []),
        preferred_locations=list(profile.preferred_locations or []),
        min_experience_years=profile.min_experience_years or 2.0,
        resume_text=raw_text,
    )


def _weights_from_profile(profile: UserProfile) -> Weights:
    return Weights(
        skills=profile.weight_skills,
        role=profile.weight_role,
        experience=profile.weight_experience,
        location=profile.weight_location,
    )


def _maybe_semantic(cand: CandidateProfile, job: Job) -> float | None:
    if not settings.ENABLE_SEMANTIC:
        return None
    from app.matching.semantic import semantic_similarity

    # Build a compact resume representation; prefer full text, fall back to skills.
    resume_text = cand.resume_text or ""
    if cand.skills:
        resume_text = (resume_text + "\nSkills: " + ", ".join(cand.skills)).strip()
    if cand.target_titles:
        resume_text = (resume_text + "\nTarget roles: " + ", ".join(cand.target_titles)).strip()
    if not resume_text:
        return None
    job_text = f"{job.title}. {job.description or ''}"
    return semantic_similarity(resume_text, job_text)


def score_single_job(db: Session, job: Job, profile: UserProfile, commit: bool = True) -> MatchResult:
    cand = _candidate_from_profile(profile)
    posting = JobPosting(
        title=job.title,
        description=job.description or "",
        location=job.location,
        required_skills=list(job.required_skills or []),
        preferred_skills=list(job.preferred_skills or []),
        experience_min=job.experience_min,
        experience_max=job.experience_max,
    )
    semantic = _maybe_semantic(cand, job)
    result = score_job(
        cand, posting, _weights_from_profile(profile),
        min_match_score=profile.min_match_score, semantic_score=semantic,
        semantic_blend=settings.SEMANTIC_BLEND,
    )

    mr = job.match_result or MatchResult(job_id=job.id)
    mr.score = result.score
    mr.skills_score = result.skills_score
    mr.role_score = result.role_score
    mr.experience_score = result.experience_score
    mr.location_score = result.location_score
    mr.semantic_score = result.semantic_score
    mr.matched_skills = result.matched_skills
    mr.missing_skills = result.missing_skills
    mr.evidence = result.evidence
    mr.mandatory_failures = result.mandatory_failures
    mr.eligible = result.eligible
    mr.explanation = result.explanation
    mr.details = result.details

    if job.match_result is None:
        db.add(mr)
        job.match_result = mr

    job.match_score = result.score
    # Status progression: eligible jobs become "eligible"; others "scored".
    if result.eligible:
        if job.status in ("discovered", "scored"):
            job.status = "eligible"
    else:
        if job.status in ("discovered",):
            job.status = "scored"

    if commit:
        db.commit()
        db.refresh(mr)
    return mr


def rescore_all(db: Session, profile: UserProfile) -> int:
    from sqlalchemy import select

    jobs = db.scalars(select(Job)).all()
    for job in jobs:
        score_single_job(db, job, profile, commit=False)
    db.commit()
    return len(jobs)
