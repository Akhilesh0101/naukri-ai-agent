"""Create the target PostgreSQL database if it does not exist.

Reads DATABASE_URL from the environment / .env, connects to the server's
default 'postgres' maintenance database using the same credentials, and issues
CREATE DATABASE <name> if missing. Safe to run repeatedly (idempotent).

Usage (from backend/):
    ./.venv/Scripts/python.exe -m scripts.create_database
"""
from __future__ import annotations

import sys
from urllib.parse import urlparse

from app.core.config import settings


def main() -> int:
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        print("DATABASE_URL is SQLite; no server-side database to create.")
        return 0

    parsed = urlparse(url.replace("postgresql+psycopg", "postgresql"))
    db_name = (parsed.path or "/naukri_agent").lstrip("/")
    if not db_name:
        print("ERROR: no database name in DATABASE_URL.")
        return 1

    # Connect to the maintenance DB 'postgres'.
    admin_dsn = parsed._replace(path="/postgres").geturl()

    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg not installed. Run: pip install -r requirements.txt")
        return 1

    try:
        with psycopg.connect(admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                exists = cur.fetchone() is not None
                if exists:
                    print(f"Database '{db_name}' already exists. Nothing to do.")
                    return 0
                # Identifier cannot be parameterized; validate to be safe.
                if not db_name.replace("_", "").isalnum():
                    print(f"ERROR: refusing unusual database name '{db_name}'.")
                    return 1
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f"Created database '{db_name}'.")
        return 0
    except Exception as exc:
        print(f"ERROR: could not create database: {exc}")
        print("Check your DATABASE_URL credentials and that PostgreSQL is running.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
