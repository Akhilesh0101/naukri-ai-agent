"""API-level tests via FastAPI TestClient (SQLite-backed)."""
from __future__ import annotations


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_db(client):
    r = client.get("/api/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"
    assert r.json()["auto_submit_enabled"] is False


def test_profile_defaults(client):
    r = client.get("/api/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["min_match_score"] == 75
    assert "Generative AI Engineer" in data["target_titles"]


def test_profile_update(client):
    r = client.put("/api/profile", json={"min_match_score": 80, "skills": ["Python", "RAG"]})
    assert r.status_code == 200
    assert r.json()["min_match_score"] == 80


def test_create_job_and_dedupe(client):
    payload = {
        "title": "AI Engineer", "company": "Acme", "location": "Remote - India",
        "description": "Python RAG LLM", "url": "https://naukri.com/j/xyz",
        "experience_min": 1, "experience_max": 4,
        "required_skills": ["Python", "RAG", "LLM"],
    }
    r = client.post("/api/jobs", json=payload)
    assert r.status_code == 201
    job = r.json()
    assert job["match_result"] is not None
    # Duplicate -> 409.
    r2 = client.post("/api/jobs", json=payload)
    assert r2.status_code == 409


def test_sample_sync_and_list(client):
    client.put("/api/profile", json={"skills": ["Python", "RAG", "LLM", "FastAPI"], "experience_years": 2})
    r = client.post("/api/sources/sample/sync")
    assert r.status_code == 200
    assert r.json()["jobs_new"] >= 1
    r2 = client.get("/api/jobs", params={"page": 1, "page_size": 50})
    assert r2.status_code == 200
    assert r2.json()["total"] >= 1


def test_url_search_validation_rejects_bad_domain(client):
    r = client.post("/api/search/url", json={"url": "https://evil.example.com/jobs"})
    assert r.status_code == 200
    body = r.json()
    assert body["accessible"] is False
    assert "allowlist" in (body["reason"] or "").lower()


def test_overview_stats(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert "total_jobs" in body
    assert body["auto_submit_enabled"] is False


def test_providers_lists_manual_fallback(client):
    r = client.get("/api/applications/providers")
    assert r.status_code == 200
    keys = [p["key"] for p in r.json()]
    assert "manual_fallback" in keys


def test_monitoring_warns_when_auto_submit_disabled(client):
    r = client.get("/api/monitoring")
    assert r.status_code == 200
    assert r.json()["auto_submit_effective"] is False
    assert r.json()["warning"]


def test_apply_endpoint_routes_to_manual(client):
    client.put("/api/profile", json={"skills": ["Python", "RAG", "LLM", "FastAPI"], "experience_years": 2})
    client.post("/api/sources/sample/sync")
    jobs = client.get("/api/jobs", params={"status": "eligible", "page_size": 50}).json()["items"]
    assert jobs, "expected at least one eligible job"
    job_id = jobs[0]["id"]
    r = client.post(f"/api/applications/job/{job_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "needs_attention"
