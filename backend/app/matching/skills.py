"""Skill normalization and alias resolution.

Maps many surface forms to a single canonical skill so that, e.g.,
"retrieval-augmented generation", "retrieval augmented generation" and "RAG"
all resolve to the canonical token "rag". This avoids double-counting and
improves recall when comparing a resume against a job description.
"""
from __future__ import annotations

import re

# canonical -> list of aliases (all compared lower-cased)
_ALIAS_GROUPS: dict[str, list[str]] = {
    "rag": [
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation",
        "retrieval augmented-generation",
    ],
    "llm": ["llm", "llms", "large language model", "large language models"],
    "genai": ["genai", "generative ai", "gen ai", "generative-ai"],
    "agentic ai": ["agentic ai", "agentic", "ai agents", "agent frameworks"],
    "python": ["python", "python3", "py"],
    "fastapi": ["fastapi", "fast api"],
    "langchain": ["langchain", "lang chain"],
    "langgraph": ["langgraph", "lang graph"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "nlp": ["nlp", "natural language processing"],
    "ml": ["ml", "machine learning"],
    "deep learning": ["deep learning", "dl"],
    "vector database": [
        "vector database",
        "vector db",
        "vector store",
        "pinecone",
        "weaviate",
        "milvus",
        "qdrant",
        "faiss",
        "chromadb",
        "chroma",
        "pgvector",
    ],
    "postgresql": ["postgresql", "postgres", "psql", "postgre sql"],
    "sql": ["sql"],
    "docker": ["docker", "containers", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "rest api": ["rest api", "rest apis", "restful", "rest"],
    "transformers": ["transformers", "hugging face", "huggingface"],
    "embeddings": ["embeddings", "sentence transformers", "sentence-transformers"],
    "prompt engineering": ["prompt engineering", "prompting"],
    "fine-tuning": ["fine-tuning", "fine tuning", "finetuning", "lora", "peft"],
    "mlops": ["mlops", "ml ops"],
    "git": ["git", "github", "gitlab", "version control"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "node.js": ["node.js", "nodejs", "node"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "spark": ["spark", "pyspark", "apache spark"],
    "airflow": ["airflow", "apache airflow"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous delivery"],
}

# Build reverse lookup: alias -> canonical
_ALIAS_TO_CANON: dict[str, str] = {}
for _canon, _aliases in _ALIAS_GROUPS.items():
    for _a in _aliases:
        _ALIAS_TO_CANON[_a] = _canon
    _ALIAS_TO_CANON.setdefault(_canon, _canon)


def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[‐-―]", "-", text)  # normalize dashes
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_skill(skill: str) -> str:
    """Return the canonical form of a single skill string."""
    s = _clean(skill)
    if s in _ALIAS_TO_CANON:
        return _ALIAS_TO_CANON[s]
    # strip trailing plural 's' as a last resort
    if s.endswith("s") and s[:-1] in _ALIAS_TO_CANON:
        return _ALIAS_TO_CANON[s[:-1]]
    return s


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize and de-duplicate a list of skills, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for sk in skills:
        if not sk or not sk.strip():
            continue
        c = normalize_skill(sk)
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# Known canonical skills for extraction from free text.
_KNOWN_CANON = sorted(_ALIAS_TO_CANON.keys(), key=len, reverse=True)


def extract_skills_from_text(text: str) -> list[str]:
    """Best-effort extraction of known skills mentioned in free text."""
    if not text:
        return []
    cleaned = _clean(text)
    found: set[str] = set()
    for alias in _KNOWN_CANON:
        # word-ish boundary match
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, cleaned):
            found.add(_ALIAS_TO_CANON[alias])
    return sorted(found)
