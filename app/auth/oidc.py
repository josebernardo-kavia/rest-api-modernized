"""OIDC discovery and JWKS retrieval with caching (Keycloak-compatible)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class _CacheEntry:
    value: Dict[str, Any]
    expires_at: float


_DISCOVERY_CACHE: Optional[_CacheEntry] = None
_JWKS_CACHE: Optional[_CacheEntry] = None


def _now() -> float:
    return time.time()


def _cache_get(entry: Optional[_CacheEntry]) -> Optional[Dict[str, Any]]:
    if entry is None:
        return None
    if entry.expires_at <= _now():
        return None
    return entry.value


def _cache_set(value: Dict[str, Any], ttl_seconds: int) -> _CacheEntry:
    return _CacheEntry(value=value, expires_at=_now() + ttl_seconds)


def _resolve_issuer(settings: Settings) -> str:
    """Resolve issuer URL from current settings, allowing deprecated KEYCLOAK_* fallbacks."""
    issuer = (settings.OIDC_ISSUER_URL or "").strip()
    if not issuer:
        issuer = (settings.KEYCLOAK_ISSUER_URL or "").strip()
    return issuer.rstrip("/")


# PUBLIC_INTERFACE
async def fetch_oidc_discovery(
    *, settings: Optional[Settings] = None, http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Fetch and cache the OIDC discovery document.

    This calls:
        {OIDC_ISSUER_URL}/.well-known/openid-configuration

    Args:
        settings: Optional Settings override.
        http_client: Optional shared httpx AsyncClient.

    Returns:
        The discovery JSON document (dict).

    Raises:
        RuntimeError: If OIDC_ISSUER_URL is not configured or discovery fetch fails.
    """
    global _DISCOVERY_CACHE  # noqa: PLW0603

    resolved_settings = settings or get_settings()
    cached = _cache_get(_DISCOVERY_CACHE)
    if cached is not None:
        return cached

    issuer = _resolve_issuer(resolved_settings)
    if not issuer:
        raise RuntimeError("OIDC_ISSUER_URL is not configured.")

    discovery_url = f"{issuer}/.well-known/openid-configuration"
    close_client = False
    client = http_client
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        close_client = True

    try:
        resp = await client.get(discovery_url, headers={"Accept": "application/json"})
        resp.raise_for_status()
        doc = resp.json()
        if not isinstance(doc, dict):
            raise RuntimeError("OIDC discovery response was not a JSON object.")
        _DISCOVERY_CACHE = _cache_set(doc, resolved_settings.OIDC_CACHE_TTL_SECONDS)
        return doc
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError(f"Failed to fetch OIDC discovery from {discovery_url}: {exc}") from exc
    finally:
        if close_client:
            await client.aclose()


# PUBLIC_INTERFACE
async def fetch_jwks(
    *, settings: Optional[Settings] = None, http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Fetch and cache JSON Web Key Set (JWKS) for token signature verification.

    The JWKS URI is read from OIDC discovery's `jwks_uri`.

    Args:
        settings: Optional Settings override.
        http_client: Optional shared httpx AsyncClient.

    Returns:
        JWKS JSON document.

    Raises:
        RuntimeError: If JWKS fetch fails or discovery is misconfigured.
    """
    global _JWKS_CACHE  # noqa: PLW0603

    resolved_settings = settings or get_settings()
    cached = _cache_get(_JWKS_CACHE)
    if cached is not None:
        return cached

    discovery = await fetch_oidc_discovery(settings=resolved_settings, http_client=http_client)
    jwks_uri = discovery.get("jwks_uri")
    if not isinstance(jwks_uri, str) or not jwks_uri.strip():
        raise RuntimeError("OIDC discovery did not include a valid 'jwks_uri'.")

    close_client = False
    client = http_client
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        close_client = True

    try:
        resp = await client.get(jwks_uri, headers={"Accept": "application/json"})
        resp.raise_for_status()
        jwks = resp.json()
        if not isinstance(jwks, dict):
            raise RuntimeError("JWKS response was not a JSON object.")
        _JWKS_CACHE = _cache_set(jwks, resolved_settings.OIDC_CACHE_TTL_SECONDS)
        return jwks
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError(f"Failed to fetch JWKS from {jwks_uri}: {exc}") from exc
    finally:
        if close_client:
            await client.aclose()


# PUBLIC_INTERFACE
def clear_oidc_caches() -> None:
    """
    PUBLIC_INTERFACE
    Clear in-memory OIDC discovery and JWKS caches.

    Useful for tests or when forcing refresh.
    """
    global _DISCOVERY_CACHE, _JWKS_CACHE  # noqa: PLW0603
    _DISCOVERY_CACHE = None
    _JWKS_CACHE = None
