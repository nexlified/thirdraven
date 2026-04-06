"""extend shopping list tables

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2026-04-06 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "i5j6k7l8m9n0"
down_revision: str | Sequence[str] | None = "h4i5j6k7l8m9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename shopping_list_item.name -> raw_name
    op.alter_column("shopping_list_item", "name", new_column_name="raw_name")

    # Add new columns to shopping_list
    op.add_column(
        "shopping_list",
        sa.Column("store_name", sa.String(), nullable=True),
    )
    op.add_column(
        "shopping_list",
        sa.Column("planned_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "shopping_list",
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "shopping_list",
        sa.Column("completed_on", sa.Date(), nullable=True),
    )

    # Add actual_price to shopping_list_item
    op.add_column(
        "shopping_list_item",
        sa.Column("actual_price", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shopping_list_item", "actual_price")
    op.drop_column("shopping_list", "completed_on")
    op.drop_column("shopping_list", "is_completed")
    op.drop_column("shopping_list", "planned_date")
    op.drop_column("shopping_list", "store_name")
    op.alter_column("shopping_list_item", "raw_name", new_column_name="name")
