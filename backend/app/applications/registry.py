"""Provider registry. Only verified providers may be used for live submission."""
from __future__ import annotations

from app.applications.base import ApplicationProvider
from app.applications.manual import ManualFallbackProvider

_PROVIDERS: dict[str, ApplicationProvider] = {
    ManualFallbackProvider.key: ManualFallbackProvider(),
}


def get_provider(key: str | None = None) -> ApplicationProvider:
    if key and key in _PROVIDERS:
        return _PROVIDERS[key]
    # Default is always the safe manual fallback.
    return _PROVIDERS[ManualFallbackProvider.key]


def list_providers() -> list[dict]:
    return [
        {
            "key": p.key,
            "name": p.name,
            "supports_auto_submit": p.supports_auto_submit,
            "verified": p.verify()[0],
            "message": p.verify()[1],
        }
        for p in _PROVIDERS.values()
    ]
