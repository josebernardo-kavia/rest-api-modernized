"""Initial placeholder migration.

Revision ID: 0001_initial_placeholder
Revises:
Create Date: 2026-01-28

This is a no-op baseline migration. Future model additions can be captured via
`alembic revision --autogenerate`.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_placeholder"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration (no-op)."""
    # No tables yet.
    pass


def downgrade() -> None:
    """Revert the migration (no-op)."""
    # No tables yet.
    pass
