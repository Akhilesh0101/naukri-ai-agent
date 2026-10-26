"""Optional local semantic similarity for resume-to-job matching.

Two free, fully-local providers (selected via EMBEDDING_PROVIDER):

  - "ollama"                : uses a local Ollama embedding model
                             (default nomic-embed-text). No large Python
                             download; requires the Ollama app running.
  - "sentence_transformers" : uses sentence-transformers (downloads a model on
                             first use; needs torch).

Everything is OFF by default (ENABLE_SEMANTIC=false). If the selected provider
is unavailable, the matching engine silently falls back to the deterministic
score only. No paid API is ever involved.
"""
from __future__ import annotations

import hashlib
import math
from collections import OrderedDict

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---- sentence-transformers (lazy, optional) ----
_st_model = None
_st_failed = False

# ---- small bounded embedding cache (avoids re-embedding the same resume) ----
_EMB_CACHE: "OrderedDict[str, list[float]]" = OrderedDict()
_EMB_CACHE_MAX = 256


def _cache_key(provider: str, model: str, text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
    return f"{provider}:{model}:{h}"


def _cache_get(key: str):
    if key in _EMB_CACHE:
        _EMB_CACHE.move_to_end(key)
        return _EMB_CACHE[key]
    return None


def _cache_put(key: str, value: list[float]) -> None:
    _EMB_CACHE[key] = value
    _EMB_CACHE.move_to_end(key)
    while len(_EMB_CACHE) > _EMB_CACHE_MAX:
        _EMB_CACHE.popitem(last=False)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _ollama_embed(text: str, model: str, base_url: str) -> list[float] | None:
    key = _cache_key("ollama", model, text)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=settings.FETCH_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        emb = resp.json().get("embedding")
        if emb:
            _cache_put(key, emb)
            return emb
        return None
    except Exception as exc:
        logger.warning("Ollama embedding failed (%s). Falling back to deterministic only.", exc)
        return None


def _st_embed(texts: list[str], model_name: str):
    global _st_model, _st_failed
    if _st_failed:
        return None
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            _st_model = SentenceTransformer(model_name)
            logger.info("Loaded sentence-transformers model: %s", model_name)
        except Exception as exc:  # pragma: no cover - optional dep
            _st_failed = True
            logger.warning("sentence-transformers unavailable (%s).", exc)
            return None
    try:
        return _st_model.encode(texts, normalize_embeddings=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("sentence-transformers encode failed: %s", exc)
        return None


def semantic_similarity(text_a: str, text_b: str, model_name: str | None = None) -> float | None:
    """Return cosine similarity in [0, 100], or None if unavailable.

    `model_name` is accepted for backward compatibility; the active provider and
    its model come from settings.
    """
    if not text_a or not text_b:
        return None

    provider = (settings.EMBEDDING_PROVIDER or "ollama").lower()

    if provider == "ollama":
        model = settings.OLLAMA_EMBEDDING_MODEL
        ea = _ollama_embed(text_a, model, settings.OLLAMA_BASE_URL)
        eb = _ollama_embed(text_b, model, settings.OLLAMA_BASE_URL)
        if ea is None or eb is None:
            return None
        sim = _cosine(ea, eb)
    else:
        model = model_name or settings.EMBEDDING_MODEL
        embs = _st_embed([text_a, text_b], model)
        if embs is None:
            return None
        sim = _cosine(list(embs[0]), list(embs[1]))

    sim = max(0.0, min(1.0, sim))
    return round(sim * 100.0, 2)


def provider_status() -> dict:
    """Report whether the configured semantic provider is reachable."""
    provider = (settings.EMBEDDING_PROVIDER or "ollama").lower()
    if not settings.ENABLE_SEMANTIC:
        return {"enabled": False, "provider": provider, "available": False,
                "detail": "ENABLE_SEMANTIC=false"}
    if provider == "ollama":
        emb = _ollama_embed("ping", settings.OLLAMA_EMBEDDING_MODEL, settings.OLLAMA_BASE_URL)
        ok = emb is not None
        return {
            "enabled": True, "provider": "ollama",
            "model": settings.OLLAMA_EMBEDDING_MODEL, "available": ok,
            "detail": "ok" if ok else "Ollama not reachable or model missing",
        }
    embs = _st_embed(["ping"], settings.EMBEDDING_MODEL)
    ok = embs is not None
    return {
        "enabled": True, "provider": "sentence_transformers",
        "model": settings.EMBEDDING_MODEL, "available": ok,
        "detail": "ok" if ok else "sentence-transformers not installed",
    }
