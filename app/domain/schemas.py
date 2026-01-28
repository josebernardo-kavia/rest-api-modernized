"""Pydantic schemas for core domain resources."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    """A simple list envelope with pagination metadata."""

    items: List[T] = Field(..., description="Page of items.")
    total: int = Field(..., ge=0, description="Total number of items matching the filter.")
    limit: int = Field(..., ge=1, le=500, description="Requested page size.")
    offset: int = Field(..., ge=0, description="Requested page offset.")


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name.")
    description: Optional[str] = Field(default=None, description="Project description.")


class ProjectCreate(ProjectBase):
    """Request payload for creating a project."""


class ProjectUpdate(BaseModel):
    """Request payload for updating a project (partial)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Project name.")
    description: Optional[str] = Field(default=None, description="Project description.")


class ProjectRead(ProjectBase):
    id: UUID = Field(..., description="Project id.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    project_id: UUID = Field(..., description="Owning project id.")
    title: str = Field(..., min_length=1, max_length=200, description="Task title.")
    description: Optional[str] = Field(default=None, description="Task description.")
    status: str = Field(default="open", min_length=1, max_length=50, description="Task status.")


class TaskCreate(TaskBase):
    """Request payload for creating a task."""


class TaskUpdate(BaseModel):
    """Request payload for updating a task (partial)."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Task title.")
    description: Optional[str] = Field(default=None, description="Task description.")
    status: Optional[str] = Field(default=None, min_length=1, max_length=50, description="Task status.")


class TaskRead(TaskBase):
    id: UUID = Field(..., description="Task id.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    class Config:
        from_attributes = True


class VulnerabilityBase(BaseModel):
    project_id: UUID = Field(..., description="Owning project id.")
    title: str = Field(..., min_length=1, max_length=200, description="Vulnerability title.")
    description: Optional[str] = Field(default=None, description="Vulnerability description.")
    severity: str = Field(
        default="medium",
        min_length=1,
        max_length=30,
        description="Severity label (e.g., low/medium/high/critical).",
    )
    status: str = Field(default="open", min_length=1, max_length=50, description="Vulnerability status.")


class VulnerabilityCreate(VulnerabilityBase):
    """Request payload for creating a vulnerability."""


class VulnerabilityUpdate(BaseModel):
    """Request payload for updating a vulnerability (partial)."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Vulnerability title.")
    description: Optional[str] = Field(default=None, description="Vulnerability description.")
    severity: Optional[str] = Field(default=None, min_length=1, max_length=30, description="Severity label.")
    status: Optional[str] = Field(default=None, min_length=1, max_length=50, description="Vulnerability status.")


class VulnerabilityRead(VulnerabilityBase):
    id: UUID = Field(..., description="Vulnerability id.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    class Config:
        from_attributes = True
