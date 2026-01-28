"""Health endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns a simple status response for liveness monitoring.",
    operation_id="health_check",
)
async def health_check() -> Dict[str, str]:
    """
    PUBLIC_INTERFACE
    Health check endpoint.

    Returns:
        JSON object indicating service status.
    """
    return {"status": "ok"}
