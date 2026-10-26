"""End-to-end PostgreSQL verification.

Runs the full database round-trip against the live PostgreSQL server configured
in DATABASE_URL:

  1. create the database if missing
  2. apply Alembic migrations (alembic upgrade head)
  3. seed the profile + sample jobs, score them
  4. create an application (manual-fallback path) and read everything back
  5. print a summary and exit non-zero on any failure

Usage (from backend/, with DATABASE_URL pointing at PostgreSQL):
    ./.venv/Scripts/python.exe -m scripts.verify_postgres
"""
from __future__ import annotations

import subprocess
import sys

from app.core.config import settings


def _run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> int:
    if settings.DATABASE_URL.startswith("sqlite"):
        print("DATABASE_URL is SQLite. Point it at PostgreSQL first.")
        return 1

    print(f"Target: {settings.DATABASE_URL.split('@')[-1]}")

    # 1. Create database.
    from scripts.create_database import main as create_db
    if create_db() != 0:
        return 1

    # 2. Migrate (invoke alembic as a module so it uses this venv).
    rc = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    if rc != 0:
        print("Alembic migration failed.")
        return 1

    # 3-4. Round-trip through the ORM.
    from sqlalchemy import select, text

    from app.db.session import SessionLocal
    from app.models.application import Application
    from app.models.job import Job
    from app.services.application_service import process_application
    from app.services.ingest_service import run_sync
    from app.services.profile_service import get_or_create_profile
    from app.sources.sample import SampleSource

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("\n[1/4] Connection OK.")

        profile = get_or_create_profile(db)
        profile.skills = ["Python", "RAG", "LLM", "FastAPI"]
        profile.experience_years = 2.0
        db.commit()
        print("[2/4] Profile seeded.")

        result = run_sync(db, SampleSource())
        print(f"[3/4] Sample sync: {result}")

        eligible = db.scalar(select(Job).where(Job.status == "eligible"))
        if eligible is None:
            print("No eligible job found after scoring.")
            return 1
        app_row = process_application(db, eligible)
        print(f"[4/4] Application for job {eligible.id}: status={app_row.status}, "
              f"manual_action={app_row.manual_action_required}")

        jobs = db.scalar(select(text("count(*)")).select_from(Job))
        apps = db.scalar(select(text("count(*)")).select_from(Application))
        print(f"\nPersisted: {jobs} jobs, {apps} application(s).")
        print("\nPostgreSQL end-to-end verification PASSED.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
