"""add household tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "household",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_household_created_by", "household", ["created_by"])

    op.create_table(
        "household_member",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["household.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_household_member_user_id"),
    )
    op.create_index(
        "ix_household_member_household_id", "household_member", ["household_id"]
    )
    op.create_index("ix_household_member_user_id", "household_member", ["user_id"])

    op.add_column(
        "person",
        sa.Column(
            "visibility", sa.String(), nullable=False, server_default="private"
        ),
    )
    op.add_column("person", sa.Column("household_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_person_household_id", "person", "household", ["household_id"], ["id"]
    )
    op.create_index("ix_person_household_id", "person", ["household_id"])

    op.add_column(
        "organization",
        sa.Column(
            "visibility", sa.String(), nullable=False, server_default="private"
        ),
    )
    op.add_column(
        "organization", sa.Column("household_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_organization_household_id",
        "organization",
        "household",
        ["household_id"],
        ["id"],
    )
    op.create_index(
        "ix_organization_household_id", "organization", ["household_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_organization_household_id", table_name="organization")
    op.drop_constraint(
        "fk_organization_household_id", "organization", type_="foreignkey"
    )
    op.drop_column("organization", "household_id")
    op.drop_column("organization", "visibility")

    op.drop_index("ix_person_household_id", table_name="person")
    op.drop_constraint("fk_person_household_id", "person", type_="foreignkey")
    op.drop_column("person", "household_id")
    op.drop_column("person", "visibility")

    op.drop_index("ix_household_member_user_id", table_name="household_member")
    op.drop_index(
        "ix_household_member_household_id", table_name="household_member"
    )
    op.drop_table("household_member")

    op.drop_index("ix_household_created_by", table_name="household")
    op.drop_table("household")
