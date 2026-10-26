from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.services.activity_service import log_activity
from app.services.profile_service import get_or_create_profile, update_profile

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MonitoringConfig(BaseModel):
    monitoring_enabled: bool | None = None
    poll_interval_minutes: int | None = None
    min_match_score: float | None = None
    auto_submit_enabled: bool | None = None


@router.get("")
def get_monitoring(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return {
        "monitoring_enabled": profile.monitoring_enabled,
        "poll_interval_minutes": profile.poll_interval_minutes,
        "min_match_score": profile.min_match_score,
        "auto_submit_enabled": profile.auto_submit_enabled,
        "auto_submit_globally_enabled": settings.AUTO_SUBMIT_ENABLED,
        "auto_submit_effective": settings.AUTO_SUBMIT_ENABLED and profile.auto_submit_enabled,
        "warning": (
            None if settings.AUTO_SUBMIT_ENABLED
            else "Automatic submission is disabled at the system level (AUTO_SUBMIT_ENABLED=false) "
                 "until an authorized provider is verified. Applications route to manual action."
        ),
    }


@router.put("")
def set_monitoring(cfg: MonitoringConfig, db: Session = Depends(get_db)):
    data = cfg.model_dump(exclude_unset=True)
    profile = update_profile(db, data)
    if "poll_interval_minutes" in data:
        try:
            from app.services.scheduler import reschedule
            reschedule(profile.poll_interval_minutes)
        except Exception:
            pass
    log_activity(db, f"Monitoring config updated: {data}", category="system")
    return get_monitoring(db)
