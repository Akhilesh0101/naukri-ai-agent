from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.matching.semantic import provider_status, semantic_similarity

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.get("")
def status():
    return {
        "enable_semantic": settings.ENABLE_SEMANTIC,
        "blend_weight": settings.SEMANTIC_BLEND,
        **provider_status(),
    }


@router.post("/similarity")
def similarity(payload: dict):
    """Debug helper: cosine similarity (0-100) between two texts, or None."""
    a = payload.get("text_a", "")
    b = payload.get("text_b", "")
    return {"similarity": semantic_similarity(a, b)}
