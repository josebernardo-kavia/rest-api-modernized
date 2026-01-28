"""Task CRUD endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser, get_current_user, require_roles
from app.common.errors import COMMON_ERROR_RESPONSES
from app.dependencies.db import get_db_session
from app.domain.errors import NotFoundError
from app.domain.schemas import ListResponse, TaskCreate, TaskRead, TaskUpdate
from app.domain.services import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    summary="Create task",
    description="Create a new task.",
    operation_id="tasks_create",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(get_current_user),
) -> TaskRead:
    """
    PUBLIC_INTERFACE
    Create a task.

    Returns:
        The created task.
    """
    svc = TaskService(db)
    try:
        task = await svc.create(
            user=user,
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
        )
        return TaskRead.model_validate(task)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "",
    summary="List tasks",
    description="List tasks with pagination and optional filtering.",
    operation_id="tasks_list",
    response_model=ListResponse[TaskRead],
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def list_tasks(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of items to return."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    project_id: Optional[UUID] = Query(default=None, description="Filter by project id."),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status."),
    q: Optional[str] = Query(default=None, description="Optional title search (case-insensitive, contains)."),
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> ListResponse[TaskRead]:
    """
    PUBLIC_INTERFACE
    List tasks.

    Returns:
        A paginated list envelope.
    """
    svc = TaskService(db)
    items, total = await svc.list(
        limit=limit,
        offset=offset,
        project_id=project_id,
        status=status_filter,
        q=q,
    )
    return ListResponse[TaskRead](
        items=[TaskRead.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{task_id}",
    summary="Get task",
    description="Get a task by id.",
    operation_id="tasks_get",
    response_model=TaskRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: AuthenticatedUser = Security(get_current_user),
) -> TaskRead:
    """
    PUBLIC_INTERFACE
    Get a task by id.

    Returns:
        The task.
    """
    svc = TaskService(db)
    try:
        task = await svc.get(task_id=task_id)
        return TaskRead.model_validate(task)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{task_id}",
    summary="Update task",
    description="Update a task (partial).",
    operation_id="tasks_update",
    response_model=TaskRead,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(get_current_user),
) -> TaskRead:
    """
    PUBLIC_INTERFACE
    Update a task by id (partial update).

    Returns:
        Updated task.
    """
    svc = TaskService(db)
    try:
        task = await svc.update(
            user=user,
            task_id=task_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
        )
        return TaskRead.model_validate(task)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Delete a task (admin only).",
    operation_id="tasks_delete",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=COMMON_ERROR_RESPONSES,
    security=[{"BearerAuth": []}],
)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> None:
    """
    PUBLIC_INTERFACE
    Delete a task by id.

    RBAC:
        Requires role: admin OR realm-admin.

    Returns:
        None.
    """
    svc = TaskService(db)
    try:
        await svc.delete(user=user, task_id=task_id)
        return None
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
