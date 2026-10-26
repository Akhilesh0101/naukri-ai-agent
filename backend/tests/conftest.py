"""Pytest fixtures. Tests run against an isolated SQLite database — no
PostgreSQL credentials required.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Configure an isolated SQLite DB BEFORE importing app modules.
_TMP_DB = Path(tempfile.gettempdir()) / "naukri_agent_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["AUTO_SUBMIT_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402,F401
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
