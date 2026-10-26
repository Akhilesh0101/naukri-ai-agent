"""Application configuration loaded from environment variables.

All settings are overridable via a .env file (see .env.example). No secrets are
hard-coded. Paid API keys are never required for core functionality.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # .../naukri-ai-agent/backend
PROJECT_ROOT = BASE_DIR.parent                   # .../naukri-ai-agent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLES_DIR = DATA_DIR / "samples"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "Naukri AI Job Application Agent"
    ENV: str = "development"
    DEBUG: bool = True
    # Local-only by default. Do NOT bind to 0.0.0.0 without adding auth.
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ---- Database ----
    # Supply your own PostgreSQL password here. Example:
    #   postgresql+psycopg://postgres:YOURPASS@127.0.0.1:5432/naukri_agent
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/naukri_agent"

    # ---- CORS (frontend origin) ----
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ---- File uploads ----
    MAX_UPLOAD_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf"]

    # ---- Matching defaults (configurable via Settings UI / preferences) ----
    MIN_MATCH_SCORE: float = 75.0
    WEIGHT_SKILLS: float = 0.45
    WEIGHT_ROLE: float = 0.25
    WEIGHT_EXPERIENCE: float = 0.20
    WEIGHT_LOCATION: float = 0.10

    # ---- Semantic similarity (optional, local, free) ----
    ENABLE_SEMANTIC: bool = False
    # Provider: "ollama" (uses a local Ollama embedding model, no big download)
    #        or "sentence_transformers" (downloads a model on first use).
    EMBEDDING_PROVIDER: str = "ollama"
    # Weight of the semantic signal when blended with the deterministic score.
    SEMANTIC_BLEND: float = 0.20
    # Model used when EMBEDDING_PROVIDER == "sentence_transformers".
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Model used when EMBEDDING_PROVIDER == "ollama".
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text:latest"

    # ---- Ollama (optional, local, free) ----
    ENABLE_OLLAMA: bool = False
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.1:latest"

    # ---- Scheduling ----
    POLL_INTERVAL_MINUTES: int = 30
    ENABLE_SCHEDULER: bool = True

    # ---- Application submission ----
    # Hard-disabled by default. Never auto-submit until an authorized provider
    # adapter is verified and this is explicitly turned on.
    AUTO_SUBMIT_ENABLED: bool = False

    # ---- Outbound fetch (URL search) safety ----
    ALLOWED_FETCH_DOMAINS: List[str] = ["naukri.com", "www.naukri.com"]
    FETCH_TIMEOUT_SECONDS: int = 15
    FETCH_MAX_BYTES: int = 5_000_000

    @field_validator("CORS_ORIGINS", "ALLOWED_UPLOAD_EXTENSIONS", "ALLOWED_FETCH_DOMAINS", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Ensure runtime dirs exist.
for _d in (DATA_DIR, UPLOAD_DIR, SAMPLES_DIR):
    _d.mkdir(parents=True, exist_ok=True)
