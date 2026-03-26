"""communication_inbox: ingest, match, auto-convert

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "communication",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False, server_default="inbound"),
        sa.Column("status", sa.String(), nullable=False, server_default="raw"),
        sa.Column("sender_identifier", sa.String(), nullable=True),
        sa.Column("recipient_identifiers", sa.JSON(), nullable=True),
        sa.Column("source_app", sa.String(), nullable=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("communicated_at", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("person_id", sa.Uuid(), nullable=True),
        sa.Column("interaction_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interaction.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_communication_owner_id", "communication", ["owner_id"])
    op.create_index("ix_communication_person_id", "communication", ["person_id"])
    op.create_index("ix_communication_status", "communication", ["status"])
    op.create_index("ix_communication_channel", "communication", ["channel"])
    op.create_index(
        "ix_communication_external_id", "communication", ["external_id"]
    )


def downgrade() -> None:
    op.drop_table("communication")
