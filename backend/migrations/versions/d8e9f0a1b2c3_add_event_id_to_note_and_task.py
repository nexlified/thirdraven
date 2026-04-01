"""add event_id to note and task

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-03-31 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("note", sa.Column("event_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_note_event_id",
        "note",
        "event",
        ["event_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("task", sa.Column("event_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_task_event_id",
        "task",
        "event",
        ["event_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_task_event_id", "task", type_="foreignkey")
    op.drop_column("task", "event_id")
    op.drop_constraint("fk_note_event_id", "note", type_="foreignkey")
    op.drop_column("note", "event_id")
