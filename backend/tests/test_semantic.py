"""Semantic blending tests. Pure math + graceful fallback; no Ollama needed."""
from __future__ import annotations

from app.matching.scorer import CandidateProfile, JobPosting, Weights, score_job


def _cand():
    return CandidateProfile(
        skills=["Python", "RAG", "LLM"], experience_years=2.0,
        target_titles=["AI Engineer"], preferred_locations=["Remote"],
    )


def _job():
    return JobPosting(
        title="AI Engineer", description="RAG LLM", location="Remote",
        required_skills=["Python", "RAG", "LLM"], experience_min=1, experience_max=4,
    )


def test_blend_zero_is_deterministic():
    det = score_job(_cand(), _job(), Weights(), semantic_score=10.0, semantic_blend=0.0)
    base = score_job(_cand(), _job(), Weights(), semantic_score=None)
    assert det.score == base.score


def test_blend_pulls_score_toward_semantic():
    high = score_job(_cand(), _job(), Weights(), semantic_score=100.0, semantic_blend=0.5)
    low = score_job(_cand(), _job(), Weights(), semantic_score=0.0, semantic_blend=0.5)
    assert high.score > low.score
    assert high.semantic_score == 100.0


def test_blend_math_exact():
    none = score_job(_cand(), _job(), Weights(), semantic_score=None).score
    blended = score_job(_cand(), _job(), Weights(), semantic_score=50.0, semantic_blend=0.2).score
    expected = round(none * 0.8 + 50.0 * 0.2, 2)
    assert abs(blended - expected) < 0.5


def test_missing_provider_returns_none(monkeypatch):
    # Force the ollama path to fail -> similarity None -> deterministic only.
    import app.matching.semantic as sem
    monkeypatch.setattr(sem.settings, "EMBEDDING_PROVIDER", "ollama", raising=False)
    monkeypatch.setattr(sem, "_ollama_embed", lambda *a, **k: None)
    assert sem.semantic_similarity("a", "b") is None
