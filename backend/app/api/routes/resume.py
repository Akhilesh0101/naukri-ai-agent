from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import UPLOAD_DIR, settings
from app.models.resume import Resume
from app.schemas.resume import ResumeOut
from app.services.activity_service import log_activity
from app.services.profile_service import get_or_create_profile
from app.services.resume_parser import parse_resume

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("", response_model=ResumeOut)
async def upload_resume(file: UploadFile, db: Session = Depends(get_db)):
    filename = file.filename or "resume.pdf"
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_UPLOAD_EXTENSIONS}")

    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.")
    if not data:
        raise HTTPException(400, "Empty file.")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(data)

    try:
        parsed = parse_resume(str(stored_path), ext)
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(422, f"Could not parse resume: {exc}") from exc

    raw_text = parsed.pop("raw_text", "")

    # Deactivate previous resumes; this one becomes active.
    for r in db.scalars(select(Resume).where(Resume.is_active.is_(True))):
        r.is_active = False

    resume = Resume(
        filename=filename,
        stored_path=str(stored_path),
        content_type=file.content_type,
        size_bytes=len(data),
        raw_text=raw_text,
        parsed=parsed,
        is_active=True,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Update profile with parsed skills/experience (user can edit later).
    profile = get_or_create_profile(db)
    if parsed.get("skills"):
        profile.skills = parsed["skills"]
    if parsed.get("experience_years") is not None:
        profile.experience_years = parsed["experience_years"]
    if parsed.get("email") and not profile.email:
        profile.email = parsed["email"]
    sp = dict(profile.structured_profile or {})
    sp.update({k: v for k, v in parsed.items() if k != "raw_text_chars"})
    sp["raw_text"] = raw_text
    profile.structured_profile = sp
    db.commit()

    log_activity(db, f"Resume uploaded and parsed: {filename}", category="resume",
                 context={"skills": len(parsed.get("skills", []))})
    return resume


@router.get("", response_model=ResumeOut | None)
def get_active_resume(db: Session = Depends(get_db)):
    resume = db.scalar(select(Resume).where(Resume.is_active.is_(True)).limit(1))
    return resume


@router.get("/list", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db)):
    return list(db.scalars(select(Resume).order_by(Resume.created_at.desc())))
