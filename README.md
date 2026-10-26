# Naukri AI Job Application Agent

A local, open-source AI agent that discovers jobs, matches them against your
resume, ranks them, and prepares applications — running entirely on your Windows
laptop with free and open-source components. No paid LLM API or paid cloud
service is required.

> **Honesty first.** This project does **not** claim a live Naukri.com
> integration. Naukri exposes no public job-search or application API, and its
> pages sit behind authentication and bot protection. The agent never bypasses
> logins, CAPTCHA, MFA, rate limits, or access controls. It ships with a working
> adapter interface plus a **sample-data** mode and an **authorized email-alert**
> importer, and clearly reports when a live source is unavailable. Automatic
> submission is **disabled by default** and stays disabled until an authorized
> application provider is implemented and verified.

---

## What it does

- **Mode A — Automatic hunting:** periodically discover jobs from configured
  sources, score each against your resume, mark eligible ones, and (when an
  authorized provider is verified and enabled) submit — otherwise prepare and
  route to manual action.
- **Mode B — URL search:** paste a Naukri job-search URL; the agent validates it
  (allowlist + SSRF protection), fetches via an authorized method, parses any
  machine-readable listings, scores and ingests them, and truthfully reports
  when a listing can't be accessed, offering fallbacks.

## Tech stack

- **Backend:** Python 3.11+/3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x, psycopg 3, Alembic, APScheduler, PyMuPDF.
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS.
- **Database:** PostgreSQL (SQLite is used only for tests).
- **AI:** deterministic hybrid matching engine; optional local `sentence-transformers` embeddings and optional local `Ollama` LLM (both off by default).

See [DEPENDENCIES.md](DEPENDENCIES.md) for versions, licenses, and resource needs.

---

## Project structure

```
naukri-ai-agent/
├─ backend/
│  ├─ app/
│  │  ├─ api/            # FastAPI routers (health, resume, jobs, sources, search, applications, …)
│  │  ├─ core/           # config, logging
│  │  ├─ db/             # SQLAlchemy base + session
│  │  ├─ models/         # ORM models (9 tables)
│  │  ├─ schemas/        # Pydantic request/response models
│  │  ├─ services/       # resume parsing, matching, ingestion, applications, scheduler, URL safety
│  │  ├─ sources/        # discovery adapters (sample, email alert, Naukri URL search) + registry
│  │  ├─ matching/       # skill normalization + hybrid scorer + optional semantic
│  │  ├─ applications/   # application-provider interface + safe manual fallback
│  │  ├─ agents/         # multi-step job-processing pipeline
│  │  └─ main.py         # FastAPI app
│  ├─ alembic/           # migrations
│  ├─ scripts/           # create_database.py, seed_sample_data.py
│  ├─ tests/             # pytest suite (SQLite-backed)
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/             # Next.js dashboard (7 pages)
├─ data/samples/         # synthetic sample jobs (clearly labeled)
├─ scripts/              # Windows PowerShell helpers
├─ docker-compose.yml    # optional: PostgreSQL only
└─ README.md
```

---

## Setup on Windows

### 0. Prerequisites

- **Python 3.11+** (3.13 tested) — `py -0` to list installed versions.
- **Node.js 18+** (26 tested) and npm.
- **PostgreSQL 15/16/17** running locally, OR use `docker compose up -d` for a
  throwaway database.

> **Note on folder names:** npm's launcher mishandles an `&` in the project path.
> This repo's `frontend/package.json` scripts already call Next through Node
> directly (`node ./node_modules/next/dist/bin/next …`) to work around it. If you
> move the project, a path **without** `&`/special characters is still safest.

### 1. Backend — configure the database

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `backend/.env` and set `DATABASE_URL` with **your** PostgreSQL password:

```
DATABASE_URL=postgresql+psycopg://postgres:YOURPASSWORD@127.0.0.1:5432/naukri_agent
```

(Your machine runs PostgreSQL 15 on port 5432 and 17 on port 5433 — pick one.)

### 2. Backend — install, create DB, migrate, run

```powershell
cd backend
py -V:3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.create_database   # creates the naukri_agent database
.\.venv\Scripts\alembic.exe upgrade head                # creates all tables
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend is now at **http://127.0.0.1:8000** (API docs at **/docs**).

Optional — load synthetic sample jobs so the dashboard has data immediately:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_sample_data
```

Optional — verify the whole PostgreSQL path in one command (creates the DB,
migrates, seeds, scores, and does an ORM round-trip):

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_postgres
```

### 3. Frontend — install and run

```powershell
cd frontend
npm install
npm run dev
```

Dashboard is now at **http://localhost:3000**. It proxies `/api/*` to the
backend on port 8000.

### One-command helpers

From the repo root (PowerShell):

```powershell
.\scripts\start-backend.ps1     # venv + install + create db + migrate + run
.\scripts\start-frontend.ps1    # install + run
.\scripts\run-tests.ps1         # backend tests
```

---

## Using the dashboard

1. **Resume & Profile** — upload your PDF resume. It's parsed locally; skills and
   experience populate your profile. Edit anything the parser got wrong. Unknown
   fields are left blank, never invented.
2. **Settings** — set target roles, minimum match score (default 75), experience
   filters, locations, polling interval, and matching weights.
3. **Auto Job Hunting** — enable monitoring, pick a polling interval, and
   "Sync all now" to pull from enabled sources (sample data works out of the box).
4. **URL Search** — paste a Naukri job-search URL to try Mode B.
5. **Jobs** — browse scored jobs with match breakdowns, matched/missing skills,
   filters, and a "Process" action for eligible jobs.
6. **Applications** — see prepared/needs-attention/submitted applications, manual
   apply links, failure reasons, and safe retry.

---

## How matching works

Hybrid, deterministic by default (weights configurable in Settings):

| Component | Default weight |
| --- | --- |
| Skills alignment | 45% |
| Role relevance | 25% |
| Experience compatibility | 20% |
| Location compatibility | 10% |

- Skills are **normalized with aliases** (e.g. "retrieval-augmented generation"
  = "RAG"), required vs preferred are distinguished, and double-counting is
  avoided.
- A score **≥ 75** qualifies a job for eligibility checks — it does **not**
  guarantee shortlisting.
- **Mandatory rules override the score:** e.g. a 10-years-minimum role is
  ineligible for a 2-year profile even if skills match perfectly.
- **Optional local semantic matching** blends resume-to-job embedding
  similarity into the score (default 20%, set by `SEMANTIC_BLEND`) when
  `ENABLE_SEMANTIC=true`. Two free, fully-local providers:
  - `EMBEDDING_PROVIDER=ollama` (default) uses your local Ollama embedding model
    (`nomic-embed-text`), no large download. Requires the Ollama app running.
  - `EMBEDDING_PROVIDER=sentence_transformers` downloads a model on first use.
  Embeddings are cached so the resume is not re-embedded for every job. If the
  provider is unreachable, scoring silently falls back to deterministic only.
  Check status at `GET /api/semantic` or on the Settings page.

---

## Application workflow & safety

States: `discovered → scored → eligible → prepared → submitting → submitted | failed | needs_attention | skipped`.

Safeguards:
- Eligibility + mandatory rules enforced before preparing.
- Duplicate submissions prevented (unique `job_id` + idempotency key).
- **`AUTO_SUBMIT_ENABLED=false`** by default (system-level lock) — eligible jobs
  are prepared and routed to **manual action** with the original job link.
- Never reports success without reliable confirmation; never invents screening
  answers or false qualifications.

To enable live auto-submit later you must: implement an `ApplicationProvider`
(see `app/applications/base.py`), verify its authorization, set
`AUTO_SUBMIT_ENABLED=true`, and turn on auto-submit in the dashboard. Until all
of that is done, the agent stays in safe manual mode.

---

## Continuous operation on Windows

The scheduler (APScheduler) runs **inside the backend process**, so monitoring
only happens while the backend is running and the laptop is on. To keep it
running:

- Keep the `uvicorn` window open, **or**
- Use **Windows Task Scheduler** to start `scripts\start-backend.ps1` at logon
  and restart on failure, **or**
- Run it as a background service with a tool like NSSM.

There is no paid cloud server involved. If the laptop sleeps or shuts down,
monitoring pauses and resumes when the backend restarts (last-sync state is
persisted).

---

## Running tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Tests use an isolated **SQLite** database, so **no PostgreSQL credentials are
needed**. They cover resume parsing, skill normalization, scoring, mandatory
eligibility, ingestion, duplicate detection, URL validation/SSRF, application
state transitions, idempotency, submission-disabled behavior, and the API.

---

## Security model

- **Localhost-only, single user, no auth** by design. The backend binds to
  `127.0.0.1`. Do **not** bind to `0.0.0.0` or expose it publicly without adding
  authentication first (the app logs a warning if a non-loopback host is set).
- `.env` holds secrets and is git-ignored; `.env.example` has no real secrets.
- Uploaded resumes, logs, and generated data are git-ignored.
- File uploads are validated (PDF only, size-limited).
- Outbound URL fetches are allowlisted and SSRF-protected (no private/loopback
  IPs, no non-http(s) schemes, redirects re-validated).
- Your Naukri password / session cookies are **never** stored. The agent does
  not log in to Naukri.
- See [DEPENDENCIES.md](DEPENDENCIES.md) for the npm advisory note.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `could not create database` / connection refused | Check `DATABASE_URL` password and that the PostgreSQL service is running (`Get-Service postgresql*`). |
| `password authentication failed` | Wrong password in `backend/.env`. |
| Frontend `Cannot find module '…\next'` | Caused by `&` in the folder path. Use the provided `npm run dev` (already calls Next via Node), or move the project to a path without special characters. |
| Port already in use | Change `--port` (backend) or `-p` (frontend), and update `NEXT_PUBLIC_API_BASE` / CORS accordingly. |
| URL search says "not accessible" | Expected for Naukri's protected pages. Use sample data, manual entry, or authorized email alerts. |
| Dashboard shows "Cannot reach backend" | Start the backend on port 8000 first. |

---

## What is verified vs. what needs authorization

- **Verified with sample data:** backend boots, PostgreSQL/SQLite connect,
  migrations apply, resume upload/parse, URL validation, matching + explanations,
  duplicate detection, application persistence, manual-action routing,
  auto-submit disabled, 38 automated tests pass, dashboard renders and talks to
  the API end-to-end.
- **Needs your authorization/credentials to go live:** a real Naukri discovery
  source and a real application-submission provider. These require a documented,
  authorized integration that does not bypass platform protections. Until then
  the agent runs in sample/manual mode and says so.
