"""Project CRUD endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser, get_current_user, require_roles
from app.common.errors import COMMON_ERROR_RESPONSES
from app.dependencies.db import get_db_session
from app.domain.schemas import ListResponse, ProjectCreate, ProjectRead, ProjectUpdate
from app.domain.services import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    summary="Create project",
    description="Create a new project (admin only).",
    operation_id="projects_create",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> ProjectRead:
    """
    PUBLIC_INTERFACE
    Create a project.

    RBAC:
        Requires role: admin OR realm-admin.

    Example request:
        {
          "name": "Acme Red Team Q1",
          "description": "Quarterly engagement tracking."
        }

    Returns:
        The created project.
    """
    svc = ProjectService(db)
    project = await svc.create(user=user, name=payload.name, description=payload.description)
    return ProjectRead.model_validate(project)


@router.get(
    "",
    summary="List projects",
    description="List projects with pagination and optional text search.",
    operation_id="projects_list",
    response_model=ListResponse[ProjectRead],
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def list_projects(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of items to return."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    q: Optional[str] = Query(default=None, description="Optional name search (case-insensitive, contains)."),
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> ListResponse[ProjectRead]:
    """
    PUBLIC_INTERFACE
    List projects.

    Returns:
        A paginated list envelope.
    """
    svc = ProjectService(db)
    items, total = await svc.list(limit=limit, offset=offset, q=q)
    return ListResponse[ProjectRead](
        items=[ProjectRead.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}",
    summary="Get project",
    description="Get a project by id.",
    operation_id="projects_get",
    response_model=ProjectRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> ProjectRead:
    """
    PUBLIC_INTERFACE
    Get a project by id.

    Returns:
        The project.

    Errors:
        - 404 (problem+json): if the project does not exist.
    """
    svc = ProjectService(db)
    project = await svc.get(project_id=project_id)
    return ProjectRead.model_validate(project)


@router.patch(
    "/{project_id}",
    summary="Update project",
    description="Update a project (admin only).",
    operation_id="projects_update",
    response_model=ProjectRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> ProjectRead:
    """
    PUBLIC_INTERFACE
    Update a project by id (partial update).

    RBAC:
        Requires role: admin OR realm-admin.

    Example request:
        { "description": "Updated description" }

    Returns:
        Updated project.

    Errors:
        - 404 (problem+json): if the project does not exist.
        - 403 (problem+json): if the user lacks required roles.
    """
    svc = ProjectService(db)
    project = await svc.update(
        user=user,
        project_id=project_id,
        name=payload.name,
        description=payload.description,
    )
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete a project (admin only).",
    operation_id="projects_delete",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> None:
    """
    PUBLIC_INTERFACE
    Delete a project by id.

    RBAC:
        Requires role: admin OR realm-admin.

    Returns:
        None.

    Errors:
        - 404 (problem+json): if the project does not exist.
        - 403 (problem+json): if the user lacks required roles.
    """
    svc = ProjectService(db)
    await svc.delete(user=user, project_id=project_id)
    return None
