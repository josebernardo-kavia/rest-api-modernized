"""Vulnerability CRUD endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser, get_current_user, require_roles
from app.common.errors import COMMON_ERROR_RESPONSES
from app.dependencies.db import get_db_session
from app.domain.schemas import (
    ListResponse,
    VulnerabilityCreate,
    VulnerabilityRead,
    VulnerabilityUpdate,
)
from app.domain.services import VulnerabilityService

router = APIRouter(prefix="/vulnerabilities", tags=["Vulnerabilities"])


@router.post(
    "",
    summary="Create vulnerability",
    description="Create a new vulnerability (finding).",
    operation_id="vulnerabilities_create",
    response_model=VulnerabilityRead,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def create_vulnerability(
    payload: VulnerabilityCreate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(get_current_user),
) -> VulnerabilityRead:
    """
    PUBLIC_INTERFACE
    Create a vulnerability.

    Example request:
        {
          "project_id": "00000000-0000-0000-0000-000000000000",
          "title": "SQL Injection in search endpoint",
          "description": "Unsanitized parameter concatenation.",
          "severity": "high",
          "status": "open"
        }

    Returns:
        The created vulnerability.

    Errors:
        - 404 (problem+json): if the referenced project does not exist.
    """
    svc = VulnerabilityService(db)
    vuln = await svc.create(
        user=user,
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
    )
    return VulnerabilityRead.model_validate(vuln)


@router.get(
    "",
    summary="List vulnerabilities",
    description="List vulnerabilities with pagination and optional filtering.",
    operation_id="vulnerabilities_list",
    response_model=ListResponse[VulnerabilityRead],
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def list_vulnerabilities(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of items to return."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    project_id: Optional[UUID] = Query(default=None, description="Filter by project id."),
    severity: Optional[str] = Query(default=None, description="Filter by severity."),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status."),
    q: Optional[str] = Query(default=None, description="Optional title search (case-insensitive, contains)."),
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> ListResponse[VulnerabilityRead]:
    """
    PUBLIC_INTERFACE
    List vulnerabilities.

    Returns:
        A paginated list envelope.
    """
    svc = VulnerabilityService(db)
    items, total = await svc.list(
        limit=limit,
        offset=offset,
        project_id=project_id,
        severity=severity,
        status=status_filter,
        q=q,
    )
    return ListResponse[VulnerabilityRead](
        items=[VulnerabilityRead.model_validate(v) for v in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{vulnerability_id}",
    summary="Get vulnerability",
    description="Get a vulnerability by id.",
    operation_id="vulnerabilities_get",
    response_model=VulnerabilityRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def get_vulnerability(
    vulnerability_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> VulnerabilityRead:
    """
    PUBLIC_INTERFACE
    Get a vulnerability by id.

    Returns:
        The vulnerability.

    Errors:
        - 404 (problem+json): if the vulnerability does not exist.
    """
    svc = VulnerabilityService(db)
    vuln = await svc.get(vulnerability_id=vulnerability_id)
    return VulnerabilityRead.model_validate(vuln)


@router.patch(
    "/{vulnerability_id}",
    summary="Update vulnerability",
    description="Update a vulnerability (partial).",
    operation_id="vulnerabilities_update",
    response_model=VulnerabilityRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def update_vulnerability(
    vulnerability_id: UUID,
    payload: VulnerabilityUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(get_current_user),
) -> VulnerabilityRead:
    """
    PUBLIC_INTERFACE
    Update a vulnerability by id (partial update).

    Example request:
        { "status": "triaged", "severity": "critical" }

    Returns:
        Updated vulnerability.

    Errors:
        - 404 (problem+json): if the vulnerability does not exist.
    """
    svc = VulnerabilityService(db)
    vuln = await svc.update(
        user=user,
        vulnerability_id=vulnerability_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
    )
    return VulnerabilityRead.model_validate(vuln)


@router.delete(
    "/{vulnerability_id}",
    summary="Delete vulnerability",
    description="Delete a vulnerability (admin only).",
    operation_id="vulnerabilities_delete",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def delete_vulnerability(
    vulnerability_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> None:
    """
    PUBLIC_INTERFACE
    Delete a vulnerability by id.

    RBAC:
        Requires role: admin OR realm-admin.

    Returns:
        None.

    Errors:
        - 404 (problem+json): if the vulnerability does not exist.
        - 403 (problem+json): if the user lacks required roles.
    """
    svc = VulnerabilityService(db)
    await svc.delete(user=user, vulnerability_id=vulnerability_id)
    return None
