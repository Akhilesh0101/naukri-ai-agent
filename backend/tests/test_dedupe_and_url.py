"""Tests for dedupe fingerprinting and URL validation/SSRF protection."""
from __future__ import annotations

import pytest

from app.services.dedupe import dedupe_hash, normalize_url
from app.services.url_safety import UrlValidationError, is_naukri_search_url, validate_url


def test_normalize_url_strips_query_and_slash():
    a = normalize_url("https://www.naukri.com/job/123?utm=abc#top")
    b = normalize_url("https://www.naukri.com/job/123/")
    assert a == b


def test_dedupe_hash_same_for_equivalent_urls():
    h1 = dedupe_hash("AI Engineer", "Acme", "https://naukri.com/j/1?ref=x")
    h2 = dedupe_hash("AI Engineer", "Acme", "https://naukri.com/j/1")
    assert h1 == h2


def test_dedupe_hash_falls_back_to_title_company():
    h1 = dedupe_hash("AI Engineer", "Acme", None)
    h2 = dedupe_hash("ai engineer", "ACME", None)
    assert h1 == h2


def test_url_rejects_non_http():
    with pytest.raises(UrlValidationError):
        validate_url("file:///etc/passwd")
    with pytest.raises(UrlValidationError):
        validate_url("gopher://naukri.com")


def test_url_rejects_non_allowlisted_domain():
    with pytest.raises(UrlValidationError):
        validate_url("https://evil.example.com/jobs")


def test_url_rejects_localhost_and_private():
    # Not in allowlist -> blocked before DNS, which is the first guard.
    with pytest.raises(UrlValidationError):
        validate_url("http://127.0.0.1:8000/")
    with pytest.raises(UrlValidationError):
        validate_url("http://localhost/")


def test_is_naukri_search_url():
    assert is_naukri_search_url("https://www.naukri.com/python-jobs")
    assert not is_naukri_search_url("https://indeed.com/jobs")
