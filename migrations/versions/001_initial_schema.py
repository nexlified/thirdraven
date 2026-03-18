"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-03-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_username", "user", ["username"], unique=True)
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "contact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contact_owner_id", "contact", ["owner_id"])

    op.create_table(
        "contact_relationship",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("from_contact_id", sa.Uuid(), nullable=False),
        sa.Column("to_contact_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["from_contact_id"], ["contact.id"]),
        sa.ForeignKeyConstraint(["to_contact_id"], ["contact.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contact_relationship_from_contact_id",
        "contact_relationship",
        ["from_contact_id"],
    )
    op.create_index(
        "ix_contact_relationship_to_contact_id",
        "contact_relationship",
        ["to_contact_id"],
    )


def downgrade() -> None:
    op.drop_table("contact_relationship")
    op.drop_table("contact")
    op.drop_table("user")
