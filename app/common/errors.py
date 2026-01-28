"""Common error responses and Problem Details model."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """
    A minimal RFC7807-like problem detail payload.

    This keeps error responses consistent across the API.
    """

    type: str = Field(default="about:blank", description="A URI reference that identifies the problem type.")
    title: str = Field(..., description="Short, human-readable summary of the problem type.")
    status: int = Field(..., description="HTTP status code.")
    detail: Optional[str] = Field(default=None, description="Human-readable explanation specific to this occurrence.")
    instance: Optional[str] = Field(default=None, description="A URI reference that identifies the specific occurrence.")


# Common reusable response documentation blocks for FastAPI.
COMMON_ERROR_RESPONSES: Dict[int, Dict[str, Any]] = {
    400: {"model": ProblemDetail, "description": "Bad Request"},
    401: {"model": ProblemDetail, "description": "Unauthorized"},
    403: {"model": ProblemDetail, "description": "Forbidden"},
    404: {"model": ProblemDetail, "description": "Not Found"},
    422: {"description": "Validation Error"},
    500: {"model": ProblemDetail, "description": "Internal Server Error"},
}
