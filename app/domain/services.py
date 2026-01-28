"""Service layer for core domain resources (business logic + authorization)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser
from app.domain.errors import NotFoundError
from app.domain.repositories import ProjectRepository, TaskRepository, VulnerabilityRepository
from app.models.domain import Project, Task, Vulnerability


def _is_admin(user: AuthenticatedUser) -> bool:
    """Best-effort check for admin-like roles (realm or client roles)."""
    return bool({"admin", "realm-admin"}.intersection(set(user.roles)))


class ProjectService:
    """Project use-cases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def create(self, *, user: AuthenticatedUser, name: str, description: Optional[str]) -> Project:
        # RBAC: creating projects is admin-only by default.
        if not _is_admin(user):
            # Let route-level dependency handle role checks generally, but keep a defense-in-depth check.
            raise PermissionError("Not authorized to create projects.")
        project = Project(name=name, description=description)
        await self._repo.create(project=project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def get(self, *, project_id: UUID) -> Project:
        project = await self._repo.get(project_id)
        if project is None:
            raise NotFoundError("Project not found.")
        return project

    async def update(
        self,
        *,
        user: AuthenticatedUser,
        project_id: UUID,
        name: Optional[str],
        description: Optional[str],
    ) -> Project:
        if not _is_admin(user):
            raise PermissionError("Not authorized to update projects.")
        project = await self.get(project_id=project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete(self, *, user: AuthenticatedUser, project_id: UUID) -> None:
        if not _is_admin(user):
            raise PermissionError("Not authorized to delete projects.")
        project = await self.get(project_id=project_id)
        await self._repo.delete(project)
        await self._session.commit()

    async def list(self, *, limit: int, offset: int, q: Optional[str]) -> tuple[list[Project], int]:
        return await self._repo.list(limit=limit, offset=offset, q=q)


class TaskService:
    """Task use-cases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaskRepository(session)
        self._projects = ProjectRepository(session)

    async def create(
        self,
        *,
        user: AuthenticatedUser,
        project_id: UUID,
        title: str,
        description: Optional[str],
        status: str,
    ) -> Task:
        # RBAC: any authenticated user can create tasks (adjust as needed).
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("Project not found.")
        task = Task(project_id=project_id, title=title, description=description, status=status)
        await self._repo.create(task=task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def get(self, *, task_id: UUID) -> Task:
        task = await self._repo.get(task_id)
        if task is None:
            raise NotFoundError("Task not found.")
        return task

    async def update(
        self,
        *,
        user: AuthenticatedUser,
        task_id: UUID,
        title: Optional[str],
        description: Optional[str],
        status: Optional[str],
    ) -> Task:
        task = await self.get(task_id=task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete(self, *, user: AuthenticatedUser, task_id: UUID) -> None:
        # RBAC: delete tasks admin-only (default).
        if not _is_admin(user):
            raise PermissionError("Not authorized to delete tasks.")
        task = await self.get(task_id=task_id)
        await self._repo.delete(task)
        await self._session.commit()

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        project_id: Optional[UUID],
        status: Optional[str],
        q: Optional[str],
    ) -> tuple[list[Task], int]:
        return await self._repo.list(limit=limit, offset=offset, project_id=project_id, status=status, q=q)


class VulnerabilityService:
    """Vulnerability use-cases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VulnerabilityRepository(session)
        self._projects = ProjectRepository(session)

    async def create(
        self,
        *,
        user: AuthenticatedUser,
        project_id: UUID,
        title: str,
        description: Optional[str],
        severity: str,
        status: str,
    ) -> Vulnerability:
        # RBAC: any authenticated user can create vulnerabilities (adjust as needed).
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("Project not found.")
        vuln = Vulnerability(
            project_id=project_id,
            title=title,
            description=description,
            severity=severity,
            status=status,
        )
        await self._repo.create(vulnerability=vuln)
        await self._session.commit()
        await self._session.refresh(vuln)
        return vuln

    async def get(self, *, vulnerability_id: UUID) -> Vulnerability:
        vuln = await self._repo.get(vulnerability_id)
        if vuln is None:
            raise NotFoundError("Vulnerability not found.")
        return vuln

    async def update(
        self,
        *,
        user: AuthenticatedUser,
        vulnerability_id: UUID,
        title: Optional[str],
        description: Optional[str],
        severity: Optional[str],
        status: Optional[str],
    ) -> Vulnerability:
        vuln = await self.get(vulnerability_id=vulnerability_id)
        if title is not None:
            vuln.title = title
        if description is not None:
            vuln.description = description
        if severity is not None:
            vuln.severity = severity
        if status is not None:
            vuln.status = status
        await self._session.commit()
        await self._session.refresh(vuln)
        return vuln

    async def delete(self, *, user: AuthenticatedUser, vulnerability_id: UUID) -> None:
        # RBAC: delete vulnerabilities admin-only (default).
        if not _is_admin(user):
            raise PermissionError("Not authorized to delete vulnerabilities.")
        vuln = await self.get(vulnerability_id=vulnerability_id)
        await self._repo.delete(vuln)
        await self._session.commit()

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        project_id: Optional[UUID],
        severity: Optional[str],
        status: Optional[str],
        q: Optional[str],
    ) -> tuple[list[Vulnerability], int]:
        return await self._repo.list(
            limit=limit,
            offset=offset,
            project_id=project_id,
            severity=severity,
            status=status,
            q=q,
        )
