"""add is_self to person and person_id to user

Revision ID: a1b2c3d4e5f6
Revises: 9545d834363c
Create Date: 2026-03-30 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9545d834363c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_self column to person table
    op.add_column(
        "person",
        sa.Column("is_self", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 2. Add person_id column to user table (nullable, no FK yet — use_alter pattern)
    op.add_column(
        "user",
        sa.Column("person_id", sa.Uuid(), nullable=True),
    )

    # 3. Add the FK constraint separately (use_alter=True equivalent)
    op.create_foreign_key(
        "fk_user_person_id",
        "user",
        "person",
        ["person_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_person_id", "user", type_="foreignkey")
    op.drop_column("user", "person_id")
    op.drop_column("person", "is_self")
