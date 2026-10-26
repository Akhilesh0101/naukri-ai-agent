"""Naukri URL-based search adapter.

IMPORTANT / HONESTY NOTE
------------------------
Naukri.com does not expose a public, unauthenticated job-search API, and its
search pages are rendered behind authentication and bot-protection. This adapter
therefore does the following, in order, and NEVER bypasses logins, CAPTCHA, or
access controls:

1. Validates the URL (scheme, allowlist, SSRF protection).
2. Attempts an authorized HTTP fetch of the public page.
3. If structured job data is present in the returned HTML (e.g. a JSON-LD or
   embedded JSON blob that Naukri serves publicly), it is parsed.
4. If the listing cannot be accessed (login wall, JS-only content, block page),
   it returns an empty result with a clear, truthful reason and suggests the
   permitted fallbacks (authorized email alerts, sample data, or a supported
   official integration).

It does not pretend to have retrieved listings it could not actually access.
"""
from __future__ import annotations

import json
import re

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger
from app.matching.skills import extract_skills_from_text
from app.services.url_safety import UrlValidationError, validate_url
from app.sources.base import RawJob

logger = get_logger(__name__)

_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


class UrlSearchResult:
    def __init__(self, jobs: list[RawJob], accessible: bool, reason: str | None):
        self.jobs = jobs
        self.accessible = accessible
        self.reason = reason


class UrlSearchSource:
    key = "url_search"
    name = "Naukri URL Search (authorized fetch)"

    def __init__(self, url: str):
        self.url = url

    def search(self) -> UrlSearchResult:
        try:
            validate_url(self.url)
        except UrlValidationError as exc:
            return UrlSearchResult([], accessible=False, reason=str(exc))

        try:
            with httpx.Client(
                timeout=settings.FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={"User-Agent": "NaukriAIAgent/0.1 (personal; authorized use)"},
            ) as client:
                resp = client.get(self.url)
        except httpx.HTTPError as exc:
            return UrlSearchResult([], accessible=False, reason=f"Fetch failed: {exc}")

        if resp.status_code in (401, 403):
            return UrlSearchResult(
                [], accessible=False,
                reason=(
                    f"Access restricted (HTTP {resp.status_code}). The listing requires "
                    "authentication or is protected. Login/CAPTCHA are never bypassed. "
                    "Use authorized email alerts or sample data instead."
                ),
            )
        if resp.status_code >= 400:
            return UrlSearchResult(
                [], accessible=False, reason=f"HTTP {resp.status_code} from source."
            )

        content = resp.text[: settings.FETCH_MAX_BYTES]
        jobs = self._parse_jobs(content)
        if jobs:
            return UrlSearchResult(jobs, accessible=True, reason=None)

        return UrlSearchResult(
            [], accessible=False,
            reason=(
                "The page was fetched but no machine-readable job listings were found. "
                "Naukri search results are rendered client-side behind authentication, "
                "so public scraping is not reliable and is not attempted. "
                "Fallback: import authorized job-alert emails, add jobs manually, "
                "or use sample data."
            ),
        )

    def _parse_jobs(self, html: str) -> list[RawJob]:
        """Parse JSON-LD JobPosting blocks if the page serves them publicly."""
        jobs: list[RawJob] = []
        for idx, block in enumerate(_JSON_LD_RE.findall(html)):
            try:
                data = json.loads(block.strip())
            except json.JSONDecodeError:
                continue
            for node in self._iter_job_nodes(data):
                raw = self._node_to_rawjob(node, idx)
                if raw:
                    jobs.append(raw)
        return jobs

    def _iter_job_nodes(self, data):
        if isinstance(data, list):
            for d in data:
                yield from self._iter_job_nodes(d)
        elif isinstance(data, dict):
            if data.get("@type") in ("JobPosting", "JobPostingList"):
                yield data
            for v in data.values():
                if isinstance(v, (list, dict)):
                    yield from self._iter_job_nodes(v)

    def _node_to_rawjob(self, node: dict, idx: int) -> RawJob | None:
        title = node.get("title") or node.get("name")
        if not title:
            return None
        org = node.get("hiringOrganization") or {}
        company = org.get("name") if isinstance(org, dict) else None
        loc = None
        jl = node.get("jobLocation")
        if isinstance(jl, dict):
            addr = jl.get("address", {})
            if isinstance(addr, dict):
                loc = addr.get("addressLocality") or addr.get("addressRegion")
        description = node.get("description", "") or ""
        return RawJob(
            source_key=self.key,
            source_job_id=str(node.get("identifier") or node.get("url") or f"url-{idx}-{title}"),
            title=str(title),
            company=company,
            location=loc,
            description=re.sub(r"<[^>]+>", " ", description)[:5000],
            url=node.get("url"),
            posted_text=node.get("datePosted"),
            required_skills=extract_skills_from_text(f"{title}. {description}"),
        )
