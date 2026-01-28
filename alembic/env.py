"""
Alembic environment configuration.

This env.py is configured for Async SQLAlchemy (asyncpg) and reads DATABASE_URL from
application settings (env/.env). It also imports the project's `Base` metadata so
autogenerate works once models are added.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings, get_settings
from app.db.session import _build_engine
from app.models.base import Base

# Alembic Config object, provides access to values in alembic.ini.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support.
target_metadata = Base.metadata


def _get_database_url() -> str:
    """Resolve DATABASE_URL from Settings and validate it is present."""
    settings: Settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure it in the environment/.env before running alembic."
        )
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without DB connection)."""
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic context and run migrations within a transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an AsyncEngine."""
    database_url = _get_database_url()
    connectable: AsyncEngine = _build_engine(database_url)

    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online_entrypoint() -> None:
    """Entrypoint invoked by Alembic."""
    asyncio.run(run_migrations_online())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online_entrypoint()
