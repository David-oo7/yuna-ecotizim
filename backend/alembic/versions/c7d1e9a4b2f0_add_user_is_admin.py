"""admin flag

Revision ID: c7d1e9a4b2f0
Revises: a5bf27d214b0
Create Date: 2026-11-22 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7d1e9a4b2f0"
down_revision: Union[str, None] = "a5bf27d214b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
