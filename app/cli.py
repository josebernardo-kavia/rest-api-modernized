"""
CLI utilities for local development (fixtures/seed data).

This module provides a small Typer CLI that can be invoked via:

    python -m app.cli seed

It uses the existing async SQLAlchemy session/engine configuration and relies on
DATABASE_URL being set in the environment (or .env).
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import typer
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_sessionmaker
from app.models.domain import Project, Task, Vulnerability

app = typer.Typer(
    add_completion=False,
    help="rest-api-modernized development CLI (seed/demo data).",
)


@dataclass(frozen=True)
class _SeedCounts:
    projects: int
    tasks: int
    vulnerabilities: int


def _require_database_url(settings: Settings) -> None:
    """Validate that DATABASE_URL is configured before attempting DB operations."""
    if not (settings.DATABASE_URL or "").strip():
        raise typer.BadParameter(
            "DATABASE_URL is not set. Configure it in your environment/.env before seeding."
        )


async def _truncate_all(session: AsyncSession) -> None:
    """
    Delete all rows from domain tables.

    Notes:
        - We delete in dependency order to satisfy FK constraints.
        - In Postgres, TRUNCATE ... CASCADE could be used, but delete() is portable.
    """
    await session.execute(delete(Vulnerability))
    await session.execute(delete(Task))
    await session.execute(delete(Project))


async def _has_any_data(session: AsyncSession) -> bool:
    """Return True if there are already projects/tasks/vulnerabilities present."""
    res = await session.execute(select(Project.id).limit(1))
    if res.first() is not None:
        return True
    res = await session.execute(select(Task.id).limit(1))
    if res.first() is not None:
        return True
    res = await session.execute(select(Vulnerability.id).limit(1))
    return res.first() is not None


def _seed_dataset() -> Dict[str, Sequence[dict]]:
    """
    Define a small, realistic dataset.

    We keep this as plain dicts to make it easy to tweak without importing Pydantic schemas.
    """
    projects = [
        {
            "key": "acme-cloud",
            "name": "Acme Cloud Hardening",
            "description": "Baseline security posture review and remediation tracking for Acme's cloud stack.",
        },
        {
            "key": "globex-web",
            "name": "Globex Web App Assessment",
            "description": "OWASP-style assessment of the customer portal and supporting APIs.",
        },
        {
            "key": "initech-internal",
            "name": "Initech Internal Red Team",
            "description": "Internal red team exercise focused on lateral movement and detection gaps.",
        },
    ]

    tasks = [
        # Acme Cloud
        {
            "project_key": "acme-cloud",
            "title": "Review IAM policies and roles",
            "description": "Identify overly broad permissions and define least-privilege roles.",
            "status": "in_progress",
        },
        {
            "project_key": "acme-cloud",
            "title": "Enable org-wide audit logging",
            "description": "Ensure audit logs are enabled and shipped to centralized SIEM.",
            "status": "open",
        },
        {
            "project_key": "acme-cloud",
            "title": "Rotate long-lived credentials",
            "description": "Replace static credentials with short-lived tokens / workload identity.",
            "status": "blocked",
        },
        {
            "project_key": "acme-cloud",
            "title": "Implement S3 bucket policy guardrails",
            "description": "Prevent public buckets and enforce encryption at rest.",
            "status": "done",
        },
        # Globex Web
        {
            "project_key": "globex-web",
            "title": "Threat model login + session flows",
            "description": "Document assumptions, attack surface, and abuse cases for auth flows.",
            "status": "open",
        },
        {
            "project_key": "globex-web",
            "title": "Run dynamic scan against staging",
            "description": "Baseline DAST scan with tuned rules to reduce noise.",
            "status": "in_progress",
        },
        {
            "project_key": "globex-web",
            "title": "Verify CSP and cookie flags",
            "description": "Ensure HttpOnly/Secure/SameSite and CSP headers are correctly set.",
            "status": "done",
        },
        # Initech Internal
        {
            "project_key": "initech-internal",
            "title": "Enumerate AD trust relationships",
            "description": "Map trust boundaries and privileged groups.",
            "status": "open",
        },
        {
            "project_key": "initech-internal",
            "title": "Test EDR detection on LSASS access",
            "description": "Validate alerts and response for credential dumping attempts.",
            "status": "in_review",
        },
        {
            "project_key": "initech-internal",
            "title": "Document remediation playbook",
            "description": "Create actionable remediation steps for common red team findings.",
            "status": "open",
        },
    ]

    vulnerabilities = [
        # Globex Web
        {
            "project_key": "globex-web",
            "title": "SQL Injection in search endpoint",
            "description": "User-supplied query is concatenated into SQL without parameterization.",
            "severity": "critical",
            "status": "open",
        },
        {
            "project_key": "globex-web",
            "title": "Stored XSS in profile bio",
            "description": "HTML is not sanitized before rendering in the admin dashboard.",
            "severity": "high",
            "status": "triaged",
        },
        {
            "project_key": "globex-web",
            "title": "Insecure password reset tokens",
            "description": "Reset token has low entropy and is valid for too long.",
            "severity": "high",
            "status": "in_progress",
        },
        # Acme Cloud
        {
            "project_key": "acme-cloud",
            "title": "Publicly accessible storage bucket",
            "description": "Misconfigured bucket ACL allows anonymous read access.",
            "severity": "high",
            "status": "open",
        },
        {
            "project_key": "acme-cloud",
            "title": "Over-permissive service account",
            "description": "Service account has editor privileges across the org.",
            "severity": "medium",
            "status": "triaged",
        },
        # Initech Internal
        {
            "project_key": "initech-internal",
            "title": "Weak SMB signing configuration",
            "description": "SMB signing not required on key servers, enabling relay attacks.",
            "severity": "medium",
            "status": "open",
        },
        {
            "project_key": "initech-internal",
            "title": "Excessive local admin membership",
            "description": "Too many users/groups are local admins on endpoints.",
            "severity": "low",
            "status": "accepted",
        },
    ]

    return {"projects": projects, "tasks": tasks, "vulnerabilities": vulnerabilities}


async def _insert_seed_data(session: AsyncSession) -> _SeedCounts:
    """
    Insert demo projects, tasks, vulnerabilities.

    Idempotency:
        This function assumes the caller already decided whether to reset or skip.
    """
    dataset = _seed_dataset()

    project_map: Dict[str, Project] = {}
    for p in dataset["projects"]:
        project = Project(name=str(p["name"]), description=str(p.get("description") or ""))
        session.add(project)
        project_map[str(p["key"])] = project

    # Flush to get project IDs for FK references.
    await session.flush()

    tasks_added = 0
    for t in dataset["tasks"]:
        project = project_map[str(t["project_key"])]
        task = Task(
            project_id=project.id,
            title=str(t["title"]),
            description=str(t.get("description") or ""),
            status=str(t.get("status") or "open"),
        )
        session.add(task)
        tasks_added += 1

    vulns_added = 0
    for v in dataset["vulnerabilities"]:
        project = project_map[str(v["project_key"])]
        vuln = Vulnerability(
            project_id=project.id,
            title=str(v["title"]),
            description=str(v.get("description") or ""),
            severity=str(v.get("severity") or "medium"),
            status=str(v.get("status") or "open"),
        )
        session.add(vuln)
        vulns_added += 1

    await session.commit()

    return _SeedCounts(projects=len(project_map), tasks=tasks_added, vulnerabilities=vulns_added)


# PUBLIC_INTERFACE
@app.command("seed")
def seed(
    reset: bool = typer.Option(
        False,
        "--reset",
        help="If set, deletes existing demo data (and all rows) before seeding.",
    ),
) -> None:
    """
    PUBLIC_INTERFACE
    Seed demo data for local development.

    This inserts:
      - 3 projects
      - 10 tasks (3–5 per project)
      - 7 vulnerabilities (varied severities/statuses)

    Environment:
        Requires DATABASE_URL in the environment/.env.

    Notes:
        Run migrations first:
            alembic upgrade head
    """
    settings = get_settings()
    _require_database_url(settings)

    async def _run() -> int:
        session_factory = get_sessionmaker(settings=settings)
        async with session_factory() as session:
            if reset:
                typer.echo("Reset enabled: deleting existing rows from domain tables...")
                await _truncate_all(session)
                await session.commit()
            else:
                if await _has_any_data(session):
                    typer.echo(
                        "Seed skipped: existing data found. "
                        "Use `--reset` to clear tables and reseed."
                    )
                    return 0

            counts = await _insert_seed_data(session)
            typer.echo(
                f"Seed complete: {counts.projects} projects, {counts.tasks} tasks, "
                f"{counts.vulnerabilities} vulnerabilities."
            )
            return 0

    try:
        raise SystemExit(asyncio.run(_run()))
    except KeyboardInterrupt:
        raise SystemExit(130) from None


# PUBLIC_INTERFACE
def main(argv: Optional[List[str]] = None) -> None:
    """
    PUBLIC_INTERFACE
    Entrypoint to run the Typer CLI.

    Args:
        argv: Optional argv override (primarily for tests). If None, uses sys.argv[1:].

    Returns:
        None. Exits via Typer/SystemExit.
    """
    app(prog_name="rest-api-modernized", args=argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    main()
