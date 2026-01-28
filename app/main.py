"""
FastAPI application entrypoint for rest-api-modernized.

This module defines the ASGI `app` object used by Uvicorn/Gunicorn.

Routes:
- GET /               : basic service identification
- GET /health         : health check (also mounted under API prefix)
- All API routes are mounted under Settings.API_PREFIX (default: /api)
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_routes_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.openapi.metadata import OPENAPI_TAGS
from app.routers.health import router as health_router
from app.routers.info import router as info_router


def _parse_cors_origins(origins: List[str]) -> List[str]:
    """Normalize CORS origins list (already parsed by Settings) and remove empties."""
    return [o.strip() for o in origins if isinstance(o, str) and o.strip()]


settings = get_settings()
configure_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    description="Modernized REST API backend (FastAPI) for the security operations platform.",
    version=settings.APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
)

# Correlation/request-id middleware
app.add_middleware(CorrelationIdMiddleware)

# CORS configuration:
# BACKEND_CORS_ORIGINS should be set to the web client's origin(s), e.g. ["http://localhost:5173"]
cors_origins = _parse_cors_origins(settings.BACKEND_CORS_ORIGINS)
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

# Root endpoint (not under /api) for convenience
@app.get(
    "/",
    summary="Service root",
    description="Returns service name and version.",
    tags=["Root"],
    operation_id="service_root",
)
async def service_root() -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Service root endpoint.

    Returns:
        A JSON object containing the service name and version.
    """
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


# Non-prefixed "public" health endpoint (explicit requirement)
app.include_router(health_router)

# API routers mounted under API_PREFIX
api_app = FastAPI(
    title=settings.APP_NAME,
    description="Modernized REST API backend (FastAPI) for the security operations platform.",
    version=settings.APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
)

# Include requested routers under API prefix:
api_app.include_router(api_routes_router)
api_app.include_router(health_router)
api_app.include_router(info_router)

# Mount the API app under prefix
app.mount(settings.API_PREFIX, api_app)
