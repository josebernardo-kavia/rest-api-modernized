"""OpenAPI metadata such as tags and descriptions."""

from __future__ import annotations

OPENAPI_TAGS = [
    {
        "name": "Root",
        "description": (
            "Top-level endpoints (root, API root, and general documentation helpers). "
            "All error responses use RFC7807 `application/problem+json`."
        ),
    },
    {
        "name": "Health",
        "description": "Liveness/readiness endpoints for monitoring.",
    },
    {
        "name": "Info",
        "description": "Service metadata endpoints (name, version, runtime info).",
    },
    {
        "name": "Auth",
        "description": (
            "Authentication/authorization helpers and protected example endpoints. "
            "Use the Swagger UI 'Authorize' button to set `Bearer <token>`."
        ),
    },
    {
        "name": "Projects",
        "description": (
            "Project management (CRUD, filtering, pagination). "
            "All endpoints require a Bearer token; write operations may require admin roles."
        ),
    },
    {
        "name": "Tasks",
        "description": (
            "Task management (CRUD, filtering, pagination). "
            "All endpoints require a Bearer token; delete requires admin roles."
        ),
    },
    {
        "name": "Vulnerabilities",
        "description": (
            "Vulnerability management (CRUD, filtering, pagination). "
            "All endpoints require a Bearer token; delete requires admin roles."
        ),
    },
]
