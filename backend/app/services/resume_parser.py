"""Resume parsing: extract text and a structured profile from a PDF.

Uses PyMuPDF (fitz) for text extraction and heuristic section detection. The
parser is intentionally conservative: when a field cannot be determined it is
left empty / marked unknown rather than guessed. No resume content is ever
invented.

The parser interface is extensible: register additional handlers in
`PARSERS` keyed by file extension.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Protocol

from app.core.logging_config import get_logger
from app.matching.skills import extract_skills_from_text

logger = get_logger(__name__)


class ResumeParser(Protocol):
    def extract_text(self, path: str) -> str: ...


def extract_text_pdf(path: str) -> str:
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            parts.append(page.get_text("text"))
    return "\n".join(parts)


# extension -> text extractor (extensible interface)
PARSERS: dict[str, Callable[[str], str]] = {
    ".pdf": extract_text_pdf,
}


_SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic", "qualification", "qualifications"],
    "projects": ["projects", "project", "key projects"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "accomplishments": ["achievements", "accomplishments", "awards", "certifications"],
}

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# e.g. "2 years", "2+ years", "2.5 yrs"
_EXP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)


def _split_sections(text: str) -> dict[str, str]:
    """Very lightweight section splitter based on header lines."""
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []
    for line in lines:
        stripped = line.strip().lower()
        matched_section = None
        if stripped and len(stripped) < 40:
            for sec, headers in _SECTION_HEADERS.items():
                if any(stripped == h or stripped.startswith(h) for h in headers):
                    matched_section = sec
                    break
        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_experience_years(text: str) -> float | None:
    matches = _EXP_RE.findall(text)
    if not matches:
        return None
    try:
        vals = [float(m) for m in matches]
        # Use the maximum stated years-of-experience figure as the best estimate.
        return max(vals)
    except ValueError:
        return None


def _bullet_items(text: str, limit: int = 20) -> list[str]:
    items: list[str] = []
    for raw in text.splitlines():
        line = raw.strip(" \t-*•●–").strip()
        if len(line) >= 8:
            items.append(line)
        if len(items) >= limit:
            break
    return items


def parse_resume(path: str, extension: str) -> dict[str, Any]:
    """Extract text and a structured profile from a resume file.

    Returns a dict with keys: raw_text, skills, experience_years, education,
    projects, technologies, accomplishments. Unknown fields are empty.
    """
    ext = extension.lower()
    extractor = PARSERS.get(ext)
    if extractor is None:
        raise ValueError(f"Unsupported resume format: {ext}")

    raw_text = extractor(path) or ""
    sections = _split_sections(raw_text)

    skills_text = sections.get("skills", "")
    # Combine explicit skills section with whole-doc extraction for recall.
    skills = extract_skills_from_text(skills_text + "\n" + raw_text)

    experience_years = _extract_experience_years(
        sections.get("experience", "") + "\n" + sections.get("header", "")
    )
    if experience_years is None:
        experience_years = _extract_experience_years(raw_text)

    emails = _EMAIL_RE.findall(raw_text)

    profile: dict[str, Any] = {
        "raw_text": raw_text,
        "email": emails[0] if emails else None,
        "skills": skills,
        "experience_years": experience_years,  # may be None (unknown)
        "education": _bullet_items(sections.get("education", ""), limit=10),
        "projects": _bullet_items(sections.get("projects", ""), limit=15),
        "technologies": skills,  # technologies == normalized skills here
        "accomplishments": _bullet_items(sections.get("accomplishments", ""), limit=15),
        "raw_text_chars": len(raw_text),
    }
    logger.info(
        "Parsed resume: %d chars, %d skills, experience=%s",
        len(raw_text), len(skills), experience_years,
    )
    return profile
