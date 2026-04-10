"""add api_key to user and url to reminder

Revision ID: j6k7l8m9n0o1
Revises: i5j6k7l8m9n0
Create Date: 2026-04-08 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "j6k7l8m9n0o1"
down_revision: str | Sequence[str] | None = "i5j6k7l8m9n0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add api_key to user (nullable; each user may optionally have one)
    op.add_column(
        "user",
        sa.Column("api_key", sa.String(), nullable=True),
    )
    op.create_index("ix_user_api_key", "user", ["api_key"], unique=False)

    # Add url to reminder
    op.add_column(
        "reminder",
        sa.Column("url", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reminder", "url")
    op.drop_index("ix_user_api_key", table_name="user")
    op.drop_column("user", "api_key")
