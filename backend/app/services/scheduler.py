"""Background scheduler for periodic job discovery (APScheduler).

- Configurable polling interval (from profile / settings).
- No overlapping syncs per source (max_instances=1, coalesce).
- Graceful shutdown via FastAPI lifespan.
- Recovers on restart (jobs are re-registered at startup).

Local monitoring only runs while the app process is alive. See README for how
to keep it running continuously on Windows.
"""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.logging_config import get_logger
from app.db.session import SessionLocal
from app.services.ingest_service import run_sync
from app.services.profile_service import get_or_create_profile
from app.sources.registry import build_sources

logger = get_logger(__name__)

_scheduler: BackgroundScheduler | None = None
JOB_ID = "poll_sources"


def _poll_all_sources() -> None:
    """Run enabled sources if monitoring is enabled in the profile."""
    db = SessionLocal()
    try:
        profile = get_or_create_profile(db)
        if not profile.monitoring_enabled:
            logger.info("Monitoring disabled; skipping scheduled poll.")
            return
        sources = build_sources()
        for src in sources.values():
            try:
                run_sync(db, src)
            except Exception as exc:  # isolate per-source failures
                logger.exception("Scheduled sync failed for %s: %s", src.key, exc)
    finally:
        db.close()


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler


def start_scheduler() -> None:
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled via ENABLE_SCHEDULER=false.")
        return
    if _scheduler is not None:
        return

    interval = settings.POLL_INTERVAL_MINUTES
    db = SessionLocal()
    try:
        profile = get_or_create_profile(db)
        interval = profile.poll_interval_minutes or interval
    except Exception:
        pass
    finally:
        db.close()

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _poll_all_sources,
        trigger="interval",
        minutes=max(1, interval),
        id=JOB_ID,
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started; polling every %d minute(s).", interval)


def reschedule(interval_minutes: int) -> None:
    if _scheduler is None:
        return
    _scheduler.reschedule_job(JOB_ID, trigger="interval", minutes=max(1, interval_minutes))
    logger.info("Rescheduled polling to every %d minute(s).", interval_minutes)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler shut down.")
