"""Top-level API routes that can be mounted under an API prefix."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["Root"])


@router.get(
    "/",
    summary="API root",
    description="Basic API root endpoint that returns a welcome message.",
    operation_id="api_root",
)
async def api_root() -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    API root endpoint.

    Returns:
        A JSON object with a short message indicating the API is running.
    """
    return {"message": "rest-api-modernized API is running"}


@router.get(
    "/info",
    summary="Service info (unprefixed)",
    description="Returns service metadata such as name, version, and timestamp.",
    operation_id="api_info_unprefixed",
)
async def api_info() -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Service metadata endpoint (unprefixed variant).

    Returns:
        A JSON object with service metadata.
    """
    return {
        "service": "rest-api-modernized",
        "version": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
