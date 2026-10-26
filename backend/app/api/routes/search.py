from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.job import UrlSearchIn
from app.services.activity_service import log_activity
from app.services.ingest_service import persist_jobs
from app.sources.url_search import UrlSearchSource

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/url")
def search_by_url(payload: UrlSearchIn, db: Session = Depends(get_db)):
    """Mode B: search using a Naukri URL via an authorized fetch.

    Returns retrieved listings (if any) plus a truthful accessibility report.
    Never bypasses login, CAPTCHA, or access controls.
    """
    source = UrlSearchSource(payload.url)
    result = source.search()

    ingested = {"jobs_found": 0, "jobs_new": 0, "jobs_duplicate": 0}
    if result.jobs:
        ingested = persist_jobs(db, result.jobs, score=True)

    log_activity(
        db,
        f"URL search: accessible={result.accessible}, found={len(result.jobs)}.",
        level="info" if result.accessible else "warning",
        category="search",
        context={"url": payload.url, "reason": result.reason},
    )

    return {
        "accessible": result.accessible,
        "reason": result.reason,
        "jobs_retrieved": len(result.jobs),
        "ingested": ingested,
        "fallbacks": [
            "Import authorized job-alert emails (data/email_alerts).",
            "Add jobs manually via POST /api/jobs.",
            "Use sample data: POST /api/sources/sample/sync.",
        ] if not result.accessible else [],
    }
