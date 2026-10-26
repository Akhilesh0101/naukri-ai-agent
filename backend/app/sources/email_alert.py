"""Email job-alert source (authorized integration placeholder).

This adapter parses job-alert emails that YOU have exported or that an
explicitly authorized email integration provides. It does NOT connect to any
mailbox by itself. Point it at a local directory of .eml / .txt exports.

This keeps the integration honest: live mailbox access requires you to
configure and authorize an email provider separately.
"""
from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path

from app.core.config import DATA_DIR
from app.matching.skills import extract_skills_from_text
from app.sources.base import RawJob

ALERTS_DIR = DATA_DIR / "email_alerts"


class EmailAlertSource:
    key = "email_alert"
    name = "Email Job Alerts (authorized export)"

    def fetch(self) -> list[RawJob]:
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        jobs: list[RawJob] = []
        for path in sorted(ALERTS_DIR.glob("*")):
            if path.suffix.lower() not in {".eml", ".txt"}:
                continue
            text = self._read(path)
            if not text:
                continue
            # Minimal extraction; real parsing depends on the alert format.
            title = path.stem
            jobs.append(
                RawJob(
                    source_key=self.key,
                    source_job_id=path.name,
                    title=title,
                    description=text[:5000],
                    required_skills=extract_skills_from_text(text),
                )
            )
        return jobs

    def _read(self, path: Path) -> str:
        try:
            if path.suffix.lower() == ".eml":
                with path.open("rb") as fh:
                    msg = BytesParser(policy=policy.default).parse(fh)
                body = msg.get_body(preferencelist=("plain", "html"))
                return body.get_content() if body else ""
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def health_check(self) -> tuple[str, str | None]:
        if not ALERTS_DIR.exists():
            return "unknown", "No email_alerts directory configured yet."
        count = len(list(ALERTS_DIR.glob("*")))
        return ("ok" if count else "degraded"), f"{count} alert file(s)."
