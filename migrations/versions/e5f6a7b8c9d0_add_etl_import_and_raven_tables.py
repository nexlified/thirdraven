"""add etl import and raven tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("source_format", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("raw_data", sa.Text(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=True),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_job_owner_id", "import_job", ["owner_id"])

    op.create_table(
        "import_row",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("raw_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("raven_log_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["import_job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_row_job_id", "import_row", ["job_id"])

    op.create_table(
        "raven_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("input_snapshot", sa.Text(), nullable=False),
        sa.Column("candidates_snapshot", sa.Text(), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raven_log_owner_id", "raven_log", ["owner_id"])

    op.create_table(
        "raven_question",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("import_row_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["import_job.id"]),
        sa.ForeignKeyConstraint(["import_row_id"], ["import_row.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raven_question_owner_id", "raven_question", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_raven_question_owner_id", table_name="raven_question")
    op.drop_table("raven_question")
    op.drop_index("ix_raven_log_owner_id", table_name="raven_log")
    op.drop_table("raven_log")
    op.drop_index("ix_import_row_job_id", table_name="import_row")
    op.drop_table("import_row")
    op.drop_index("ix_import_job_owner_id", table_name="import_job")
    op.drop_table("import_job")
