"""Common pagination parameters."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters used across list endpoints."""

    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of items to return.")
    offset: int = Field(default=0, ge=0, description="Number of items to skip before returning results.")
