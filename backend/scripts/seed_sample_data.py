"""Seed the sample-data source and run one sync so the dashboard has data.

Usage (from backend/):
    ./.venv/Scripts/python.exe -m scripts.seed_sample_data
"""
from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ingest_service import run_sync
from app.sources.sample import SampleSource


def main() -> int:
    db = SessionLocal()
    try:
        result = run_sync(db, SampleSource())
        print("Sample sync:", result)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
