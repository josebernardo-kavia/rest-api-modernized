"""Repository layer for core domain resources."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Project, Task, Vulnerability


class ProjectRepository:
    """DB operations for projects."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, project: Project) -> Project:
        self._session.add(project)
        await self._session.flush()
        return project

    async def get(self, project_id: UUID) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: Optional[str] = None,
    ) -> tuple[list[Project], int]:
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(Project.name.ilike(like))

        base = select(Project)
        if filters:
            for f in filters:
                base = base.where(f)

        total_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(total_stmt)).scalar_one())

        stmt = base.order_by(Project.created_at.desc()).limit(limit).offset(offset)
        items = list((await self._session.execute(stmt)).scalars().all())
        return items, total


class TaskRepository:
    """DB operations for tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, task: Task) -> Task:
        self._session.add(task)
        await self._session.flush()
        return task

    async def get(self, task_id: UUID) -> Optional[Task]:
        stmt = select(Task).where(Task.id == task_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, task: Task) -> None:
        await self._session.delete(task)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
    ) -> tuple[list[Task], int]:
        stmt = select(Task)

        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Task.title.ilike(like))

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(total_stmt)).scalar_one())

        items_stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        items = list((await self._session.execute(items_stmt)).scalars().all())
        return items, total


class VulnerabilityRepository:
    """DB operations for vulnerabilities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, vulnerability: Vulnerability) -> Vulnerability:
        self._session.add(vulnerability)
        await self._session.flush()
        return vulnerability

    async def get(self, vulnerability_id: UUID) -> Optional[Vulnerability]:
        stmt = select(Vulnerability).where(Vulnerability.id == vulnerability_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, vulnerability: Vulnerability) -> None:
        await self._session.delete(vulnerability)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        project_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
    ) -> tuple[list[Vulnerability], int]:
        stmt = select(Vulnerability)

        if project_id:
            stmt = stmt.where(Vulnerability.project_id == project_id)
        if severity:
            stmt = stmt.where(Vulnerability.severity == severity)
        if status:
            stmt = stmt.where(Vulnerability.status == status)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Vulnerability.title.ilike(like))

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(total_stmt)).scalar_one())

        items_stmt = stmt.order_by(Vulnerability.created_at.desc()).limit(limit).offset(offset)
        items = list((await self._session.execute(items_stmt)).scalars().all())
        return items, total
