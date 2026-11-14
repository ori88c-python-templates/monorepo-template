"""create feature_flags

Revision ID: 04befa978a2d
Revises:
Create Date: 2026-09-18 22:08:17.191380

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "04befa978a2d"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the feature_flags table."""
    op.create_table(
        "feature_flags",
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("value", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "name"),
    )


def downgrade() -> None:
    """Drop the feature_flags table."""
    op.drop_table("feature_flags")
