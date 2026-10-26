from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.source import JobSource, SyncHistory
from app.schemas.source import SourceOut, SyncHistoryOut, SyncResult
from app.services.ingest_service import run_sync
from app.sources.registry import SOURCE_METADATA, build_sources

router = APIRouter(prefix="/sources", tags=["sources"])


def _seed_sources(db: Session) -> None:
    existing = {s.key for s in db.scalars(select(JobSource))}
    for meta in SOURCE_METADATA:
        if meta["key"] not in existing:
            db.add(JobSource(key=meta["key"], name=meta["name"], enabled=meta["enabled"], health="unknown"))
    db.commit()


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    _seed_sources(db)
    return list(db.scalars(select(JobSource).order_by(JobSource.key)))


@router.post("/{key}/sync", response_model=SyncResult)
def sync_source(key: str, db: Session = Depends(get_db)):
    sources = build_sources()
    if key not in sources:
        raise HTTPException(404, f"No syncable source adapter '{key}'. Available: {list(sources)}")
    result = run_sync(db, sources[key])
    return result


@router.post("/sync-all", response_model=list[SyncResult])
def sync_all(db: Session = Depends(get_db)):
    sources = build_sources()
    return [run_sync(db, src) for src in sources.values()]


@router.get("/{key}/history", response_model=list[SyncHistoryOut])
def source_history(key: str, db: Session = Depends(get_db)):
    src = db.scalar(select(JobSource).where(JobSource.key == key))
    if src is None:
        raise HTTPException(404, "Source not found.")
    return list(
        db.scalars(
            select(SyncHistory).where(SyncHistory.source_id == src.id)
            .order_by(SyncHistory.created_at.desc()).limit(50)
        )
    )
