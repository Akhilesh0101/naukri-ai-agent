"""Tests for skill normalization and the matching/scoring engine."""
from __future__ import annotations

from app.matching.scorer import CandidateProfile, JobPosting, Weights, score_job
from app.matching.skills import (
    extract_skills_from_text,
    normalize_skill,
    normalize_skills,
)


def _cand(**kw):
    base = dict(
        skills=["Python", "RAG", "LLM", "FastAPI", "LangChain"],
        experience_years=2.0,
        target_titles=["Generative AI Engineer", "AI Engineer", "Machine Learning Engineer"],
        preferred_locations=["India", "Remote"],
        min_experience_years=2.0,
    )
    base.update(kw)
    return CandidateProfile(**base)


# ---- Skill normalization ----

def test_rag_alias():
    assert normalize_skill("retrieval-augmented generation") == "rag"
    assert normalize_skill("Retrieval Augmented Generation") == "rag"
    assert normalize_skill("RAG") == "rag"


def test_normalize_dedupes():
    out = normalize_skills(["Python", "python3", "PY", "RAG", "rag"])
    assert out.count("python") == 1
    assert out.count("rag") == 1


def test_extract_from_text():
    skills = extract_skills_from_text("We use Python, FastAPI and PostgreSQL with Docker.")
    assert "python" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills
    assert "docker" in skills


# ---- Scoring ----

def test_good_match_is_eligible():
    job = JobPosting(
        title="Generative AI Engineer",
        description="Build RAG pipelines with LLMs",
        location="Remote - India",
        required_skills=["Python", "RAG", "LLM"],
        preferred_skills=["FastAPI"],
        experience_min=1, experience_max=4,
    )
    r = score_job(_cand(), job, Weights(), min_match_score=75)
    assert r.score >= 75
    assert r.eligible is True
    assert "rag" in r.matched_skills
    assert r.mandatory_failures == []


def test_poor_match_not_eligible():
    job = JobPosting(
        title="Senior Java Developer",
        description="Spring Boot and Oracle",
        location="Chennai",
        required_skills=["java", "spring boot", "oracle"],
        experience_min=6, experience_max=10,
    )
    r = score_job(_cand(), job, Weights(), min_match_score=75)
    assert r.eligible is False
    assert r.score < 75


def test_senior_role_mandatory_fail_overrides_score():
    # Even with matching skills, 10y minimum vs 2y experience => ineligible.
    job = JobPosting(
        title="Machine Learning Engineer",
        description="lead ML",
        location="Remote",
        required_skills=["Python", "ML"],
        experience_min=10, experience_max=15,
    )
    r = score_job(_cand(skills=["Python", "ML"]), job, Weights(), min_match_score=75)
    assert r.eligible is False
    assert any("minimum" in f.lower() for f in r.mandatory_failures)


def test_missing_requirements_reported():
    job = JobPosting(
        title="AI Engineer",
        description="",
        location="India",
        required_skills=["Python", "RAG", "LLM", "kubernetes", "aws", "spark"],
        experience_min=1, experience_max=4,
    )
    r = score_job(_cand(skills=["Python", "RAG", "LLM"]), job, Weights())
    assert "kubernetes" in r.missing_skills
    assert "aws" in r.missing_skills


def test_unknown_experience_is_neutral():
    job = JobPosting(
        title="AI Engineer", description="", location="Remote",
        required_skills=["Python"], experience_min=2, experience_max=5,
    )
    r = score_job(_cand(experience_years=None), job, Weights())
    # Unknown experience -> neutral, not a mandatory failure.
    assert all("minimum" not in f.lower() for f in r.mandatory_failures)


def test_weights_normalized_and_configurable():
    w = Weights(skills=90, role=50, experience=40, location=20).normalized()
    total = w.skills + w.role + w.experience + w.location
    assert abs(total - 1.0) < 1e-9


def test_score_bounds():
    job = JobPosting(title="AI Engineer", required_skills=["Python"])
    r = score_job(_cand(), job, Weights())
    assert 0.0 <= r.score <= 100.0
