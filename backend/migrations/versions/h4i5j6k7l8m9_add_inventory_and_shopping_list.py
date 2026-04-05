"""add inventory and shopping list tables

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2026-04-05 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h4i5j6k7l8m9"
down_revision: str | Sequence[str] | None = "g3h4i5j6k7l8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add product_id FK to reminder table
    op.add_column(
        "reminder",
        sa.Column("product_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_reminder_product_id",
        "reminder",
        "product",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_reminder_product_id", "reminder", ["product_id"], unique=False
    )

    # Create shopping_list table
    op.create_table(
        "shopping_list",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shopping_list_owner_id"), "shopping_list", ["owner_id"], unique=False
    )

    # Create shopping_list_item table
    op.create_table(
        "shopping_list_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("list_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("estimated_price", sa.Float(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("is_checked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["list_id"], ["shopping_list.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["product.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shopping_list_item_owner_id"),
        "shopping_list_item",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopping_list_item_list_id"),
        "shopping_list_item",
        ["list_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopping_list_item_product_id"),
        "shopping_list_item",
        ["product_id"],
        unique=False,
    )

    # Create inventory_profile table
    op.create_table(
        "inventory_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("is_consumable", sa.Boolean(), nullable=False),
        sa.Column("restock_unit", sa.String(), nullable=False),
        sa.Column("reorder_threshold", sa.Float(), nullable=False),
        sa.Column("typical_monthly_usage", sa.Float(), nullable=False),
        sa.Column("current_stock", sa.Float(), nullable=False),
        sa.Column("last_restocked_on", sa.Date(), nullable=True),
        sa.Column("estimated_depletion_date", sa.Date(), nullable=True),
        sa.Column("preferred_source", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id", "product_id", name="uq_inventory_owner_product"
        ),
    )
    op.create_index(
        op.f("ix_inventory_profile_owner_id"),
        "inventory_profile",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_profile_product_id"),
        "inventory_profile",
        ["product_id"],
        unique=False,
    )

    # Create transaction_item table
    op.create_table(
        "transaction_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("raw_name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("discount", sa.Float(), nullable=False),
        sa.Column("store_name", sa.String(), nullable=True),
        sa.Column("import_batch_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["user.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transaction.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["product.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transaction_item_owner_id"),
        "transaction_item",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transaction_item_transaction_id"),
        "transaction_item",
        ["transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_transaction_item_transaction_id"), table_name="transaction_item"
    )
    op.drop_index(
        op.f("ix_transaction_item_owner_id"), table_name="transaction_item"
    )
    op.drop_table("transaction_item")

    op.drop_index(
        op.f("ix_inventory_profile_product_id"), table_name="inventory_profile"
    )
    op.drop_index(
        op.f("ix_inventory_profile_owner_id"), table_name="inventory_profile"
    )
    op.drop_table("inventory_profile")

    op.drop_index(
        op.f("ix_shopping_list_item_product_id"), table_name="shopping_list_item"
    )
    op.drop_index(
        op.f("ix_shopping_list_item_list_id"), table_name="shopping_list_item"
    )
    op.drop_index(
        op.f("ix_shopping_list_item_owner_id"), table_name="shopping_list_item"
    )
    op.drop_table("shopping_list_item")

    op.drop_index(
        op.f("ix_shopping_list_owner_id"), table_name="shopping_list"
    )
    op.drop_table("shopping_list")

    op.drop_index("ix_reminder_product_id", table_name="reminder")
    op.drop_constraint("fk_reminder_product_id", "reminder", type_="foreignkey")
    op.drop_column("reminder", "product_id")
