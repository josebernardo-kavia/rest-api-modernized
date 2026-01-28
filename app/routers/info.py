"""Service info endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["Info"])


@router.get(
    "/info",
    summary="Service info",
    description="Returns service name, version, and a server timestamp.",
    operation_id="service_info",
)
async def service_info(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Service metadata endpoint.

    Args:
        settings: Injected application settings.

    Returns:
        JSON object containing service metadata.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_prefix": settings.API_PREFIX,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
