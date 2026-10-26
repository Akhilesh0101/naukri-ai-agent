# Dependencies, licenses, and resource requirements

All components are free and open-source. No paid LLM API or paid cloud service
is required for any core functionality.

## System requirements

| Resource | Minimum | Recommended | Notes |
| --- | --- | --- | --- |
| RAM | 4 GB | 8 GB+ | 8 GB+ if you enable local embeddings or Ollama |
| Disk | 2 GB | 5 GB+ | Node modules + Python venv + PostgreSQL data |
| CPU | 2 cores | 4 cores | GPU optional, only helps Ollama / embeddings |
| GPU | none | optional | Only used by Ollama / sentence-transformers if enabled |
| OS | Windows 10/11 | Windows 11 | Also runs on macOS/Linux |

Core features (parsing, deterministic matching, ingestion, dashboard) run fine
on CPU with 4 GB RAM. Optional semantic similarity and local LLM inference are
heavier and are OFF by default.

## Backend Python packages

| Package | Version | License |
| --- | --- | --- |
| fastapi | 0.115.6 | MIT |
| uvicorn | 0.34.0 | BSD-3-Clause |
| pydantic | 2.10.4 | MIT |
| pydantic-settings | 2.7.1 | MIT |
| SQLAlchemy | 2.0.36 | MIT |
| alembic | 1.14.0 | MIT |
| psycopg (3) | 3.2.3 | LGPL-3.0 |
| PyMuPDF | 1.25.1 | AGPL-3.0 / commercial |
| APScheduler | 3.11.0 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| python-multipart | 0.0.20 | Apache-2.0 |
| pytest | 8.3.4 | MIT |
| pytest-asyncio | 0.25.0 | Apache-2.0 |

> **PyMuPDF license note:** PyMuPDF is AGPL-3.0 (or a paid commercial license).
> For personal, local, non-distributed use this is fine. If you later
> distribute this app, either comply with AGPL or swap the resume text
> extractor (`app/services/resume_parser.py` → `PARSERS`) for an MIT/BSD
> alternative such as `pypdf`. The parser interface is pluggable for exactly
> this reason.

### Optional (not installed by default)

| Package | Purpose | License |
| --- | --- | --- |
| sentence-transformers | Local semantic similarity | Apache-2.0 |
| Ollama (external app) | Local LLM inference | MIT |

## Frontend npm packages

| Package | Version | License |
| --- | --- | --- |
| next | 14.2.35 | MIT |
| react / react-dom | 18.3.1 | MIT |
| typescript | 5.5.3 | Apache-2.0 |
| tailwindcss | 3.4.6 | MIT |
| autoprefixer | 10.4.19 | MIT |
| postcss | 8.4.39 | MIT |

## Database

| Component | Version | License |
| --- | --- | --- |
| PostgreSQL | 15 / 16 / 17 | PostgreSQL License (permissive) |

## Known advisories

`npm audit` reports advisories against newer-discovered issues in Next.js and
PostCSS that are only patched in Next 15/16 and Tailwind 4 (both breaking
upgrades). They concern DoS / request-smuggling / dev-time source-map reads that
require **public network exposure** or attacker-controlled build input. This app
binds to **localhost only** for a single user, so they are not practically
exploitable in the intended deployment. If you expose the dashboard publicly,
upgrade to Next 15+ and add authentication first.
