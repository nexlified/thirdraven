"""add transaction table

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2026-04-03 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transaction",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("transacted_on", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category_term_id", sa.Uuid(), nullable=True),
        sa.Column("payment_method_term_id", sa.Uuid(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("subscription_id", sa.Uuid(), nullable=True),
        sa.Column("merchant", sa.String(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("import_batch_id", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["category_term_id"], ["term.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["payment_method_term_id"], ["term.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscription.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transaction_owner_id"), "transaction", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_transaction_owner_id_transacted_on",
        "transaction",
        ["owner_id", "transacted_on"],
        unique=False,
    )
    op.create_index(
        "ix_transaction_transaction_type",
        "transaction",
        ["transaction_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transaction_transaction_type", table_name="transaction")
    op.drop_index(
        "ix_transaction_owner_id_transacted_on", table_name="transaction"
    )
    op.drop_index(op.f("ix_transaction_owner_id"), table_name="transaction")
    op.drop_table("transaction")
