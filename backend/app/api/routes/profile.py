from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.profile import ProfileOut, ProfileUpdate
from app.services.matching_service import rescore_all
from app.services.profile_service import get_or_create_profile, update_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def read_profile(db: Session = Depends(get_db)):
    return get_or_create_profile(db)


@router.put("", response_model=ProfileOut)
def put_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    profile = update_profile(db, data)
    # Rescore jobs if any matching-relevant field changed.
    if data.keys() & {
        "skills", "experience_years", "target_titles", "preferred_locations",
        "min_experience_years", "min_match_score",
        "weight_skills", "weight_role", "weight_experience", "weight_location",
    }:
        rescore_all(db, profile)
    return profile
