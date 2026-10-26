"""Duplicate detection via URL normalization and content fingerprinting."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url.strip().lower())
    except ValueError:
        return url.strip().lower()
    # Drop query/fragment and trailing slash; keep scheme+host+path.
    path = p.path.rstrip("/")
    return urlunparse((p.scheme, p.netloc, path, "", "", ""))


def _norm_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def dedupe_hash(title: str, company: str | None, url: str | None) -> str:
    """Stable fingerprint. Prefer URL; fall back to title+company."""
    nurl = normalize_url(url)
    if nurl:
        basis = nurl
    else:
        basis = f"{_norm_text(title)}|{_norm_text(company)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:48]
