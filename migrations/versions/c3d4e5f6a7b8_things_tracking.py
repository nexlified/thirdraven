"""things_tracking: asset enrichment, tracked_record, document

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Extend asset with product/physical detail columns ──────────────────────
    for col_name in [
        "brand",
        "model_number",
        "color",
        "condition",
        "location_note",
        "barcode",
        "image_url",
        "purchase_url",
        "purchase_currency",
    ]:
        op.add_column("asset", sa.Column(col_name, sa.String(), nullable=True))

    # ── tracked_record ─────────────────────────────────────────────────────────
    op.create_table(
        "tracked_record",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("record_type_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("reference_number", sa.String(), nullable=True),
        sa.Column("issuer", sa.String(), nullable=True),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("billing_frequency", sa.String(), nullable=True),
        sa.Column("auto_renews", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("coverage_notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("person_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["record_type_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracked_record_owner_id", "tracked_record", ["owner_id"])
    op.create_index("ix_tracked_record_record_type_id", "tracked_record", ["record_type_id"])
    op.create_index("ix_tracked_record_expires_on", "tracked_record", ["expires_on"])

    # ── document ───────────────────────────────────────────────────────────────
    op.create_table(
        "document",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("doc_type_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["doc_type_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_owner_id", "document", ["owner_id"])
    op.create_index("ix_document_entity_type", "document", ["entity_type"])
    op.create_index("ix_document_entity_id", "document", ["entity_id"])


def downgrade() -> None:
    op.drop_table("document")
    op.drop_table("tracked_record")
    for col_name in [
        "brand",
        "model_number",
        "color",
        "condition",
        "location_note",
        "barcode",
        "image_url",
        "purchase_url",
        "purchase_currency",
    ]:
        op.drop_column("asset", col_name)
