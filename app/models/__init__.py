"""ORM models package.

The declarative Base is defined in `app.models.base`.

Note:
    Import domain ORM models here so Alembic can discover metadata for autogenerate.
"""

from app.models.domain import Project, Task, Vulnerability  # noqa: F401
