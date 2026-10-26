"""Resume parser tests. Generates a synthetic PDF with PyMuPDF."""
from __future__ import annotations

import fitz  # PyMuPDF

from app.services.resume_parser import parse_resume

RESUME_TEXT = """John Doe
john.doe@example.com

Summary
AI Engineer with 2 years of experience building LLM applications.

Skills
Python, FastAPI, RAG, LangChain, PostgreSQL, Docker, PyTorch

Experience
AI Engineer at Acme (2 years)
Built retrieval-augmented generation pipelines.

Education
B.Tech Computer Science

Projects
RAG chatbot using vector databases
"""


def _make_pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), RESUME_TEXT, fontsize=11)
    doc.save(str(path))
    doc.close()


def test_parse_resume_extracts_skills_and_experience(tmp_path):
    pdf = tmp_path / "resume.pdf"
    _make_pdf(pdf)
    parsed = parse_resume(str(pdf), ".pdf")
    assert parsed["raw_text_chars"] > 0
    assert "python" in parsed["skills"]
    assert "rag" in parsed["skills"]
    assert "fastapi" in parsed["skills"]
    assert parsed["experience_years"] == 2.0
    assert parsed["email"] == "john.doe@example.com"


def test_parse_resume_unknown_experience_is_none(tmp_path):
    pdf = tmp_path / "r2.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Jane\nSkills\nPython, Docker", fontsize=11)
    doc.save(str(pdf))
    doc.close()
    parsed = parse_resume(str(pdf), ".pdf")
    # No stated years -> unknown (None), never guessed.
    assert parsed["experience_years"] is None


def test_unsupported_format_raises(tmp_path):
    import pytest
    f = tmp_path / "x.docx"
    f.write_text("hi")
    with pytest.raises(ValueError):
        parse_resume(str(f), ".docx")
