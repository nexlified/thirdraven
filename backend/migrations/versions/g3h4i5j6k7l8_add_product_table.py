"""add product table

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2026-04-04 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g3h4i5j6k7l8"
down_revision: str | Sequence[str] | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("category_term_id", sa.Uuid(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("barcode", sa.String(), nullable=True),
        sa.Column("priceraven_product_id", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_term_id"], ["term.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_product_owner_id"), "product", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_product_barcode", "product", ["barcode"], unique=False
    )
    op.create_index(
        "ix_product_owner_id_name", "product", ["owner_id", "name"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_product_owner_id_name", table_name="product")
    op.drop_index("ix_product_barcode", table_name="product")
    op.drop_index(op.f("ix_product_owner_id"), table_name="product")
    op.drop_table("product")
