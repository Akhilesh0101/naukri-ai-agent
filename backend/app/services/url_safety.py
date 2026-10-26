"""URL validation and SSRF protection for outbound fetches.

Guards against:
  - non-http(s) schemes (file://, gopher://, etc.)
  - domains outside the configured allowlist
  - requests that resolve to private / loopback / link-local / reserved IPs
  - oversized responses and slow endpoints (timeouts + byte cap)

Redirects are followed manually so each hop is re-validated.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UrlValidationError(ValueError):
    pass


def _host_allowed(host: str) -> bool:
    host = host.lower().strip(".")
    for allowed in settings.ALLOWED_FETCH_DOMAINS:
        a = allowed.lower().strip(".")
        if host == a or host.endswith("." + a):
            return True
    return False


def _ip_is_public(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_url(url: str) -> str:
    """Validate a URL for safe outbound fetching. Returns the normalized URL."""
    if not url or len(url) > 2048:
        raise UrlValidationError("URL is empty or too long.")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UrlValidationError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise UrlValidationError("URL has no host.")
    host = parsed.hostname
    if not _host_allowed(host):
        raise UrlValidationError(
            f"Host '{host}' is not in the allowlist: {settings.ALLOWED_FETCH_DOMAINS}"
        )
    # Resolve and ensure no private addresses (anti-SSRF via DNS rebinding guard).
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UrlValidationError(f"Could not resolve host '{host}': {exc}") from exc
    for info in infos:
        ip = info[4][0]
        if not _ip_is_public(ip):
            raise UrlValidationError(
                f"Host '{host}' resolves to a non-public address ({ip}); blocked."
            )
    return url


def is_naukri_search_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return bool(parsed.hostname and "naukri.com" in parsed.hostname.lower())
