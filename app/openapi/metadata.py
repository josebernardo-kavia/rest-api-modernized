"""OpenAPI metadata such as tags and descriptions."""

from __future__ import annotations

OPENAPI_TAGS = [
    {
        "name": "Root",
        "description": "Top-level endpoints (root and basic service metadata).",
    },
    {
        "name": "Health",
        "description": "Liveness/readiness endpoints for monitoring.",
    },
    {
        "name": "Info",
        "description": "Service metadata endpoints (name, version, build/runtime info).",
    },
]
