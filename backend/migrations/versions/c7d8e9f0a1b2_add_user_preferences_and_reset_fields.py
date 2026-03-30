"""add user preferences and reset-password fields

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30 18:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("preferences", sa.JSON(), nullable=True))
    op.add_column(
        "user",
        sa.Column("reset_password_token_hash", sa.String(), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("reset_password_token_expires_at", sa.DateTime(), nullable=True),
    )

    op.execute("UPDATE \"user\" SET preferences = '{}' WHERE preferences IS NULL")


def downgrade() -> None:
    op.drop_column("user", "reset_password_token_expires_at")
    op.drop_column("user", "reset_password_token_hash")
    op.drop_column("user", "preferences")

