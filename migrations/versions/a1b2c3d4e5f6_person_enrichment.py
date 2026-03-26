"""person_enrichment: life events, significant dates, physical, personality, extended context/social

Revision ID: a1b2c3d4e5f6
Revises: 2232f5dfe6f0
Create Date: 2026-03-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "2232f5dfe6f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── person_context: add contact intelligence columns ──────────────────────
    op.add_column(
        "person_context", sa.Column("last_contacted_on", sa.Date(), nullable=True)
    )
    op.add_column(
        "person_context",
        sa.Column("contact_frequency_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "person_context",
        sa.Column("preferred_contact_term_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_person_context_preferred_contact_term",
        "person_context",
        "term",
        ["preferred_contact_term_id"],
        ["id"],
    )

    # ── person_social: add extended handles ───────────────────────────────────
    op.add_column(
        "person_social", sa.Column("facebook_url", sa.String(), nullable=True)
    )
    op.add_column(
        "person_social", sa.Column("github_handle", sa.String(), nullable=True)
    )
    op.add_column(
        "person_social", sa.Column("discord_handle", sa.String(), nullable=True)
    )
    op.add_column(
        "person_social", sa.Column("telegram_handle", sa.String(), nullable=True)
    )

    # ── person_physical ───────────────────────────────────────────────────────
    op.create_table(
        "person_physical",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("eye_color_term_id", sa.Uuid(), nullable=True),
        sa.Column("hair_color_term_id", sa.Uuid(), nullable=True),
        sa.Column("blood_type", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["eye_color_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["hair_color_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index("ix_person_physical_person_id", "person_physical", ["person_id"])

    # ── person_personality ────────────────────────────────────────────────────
    op.create_table(
        "person_personality",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("interests", sa.String(), nullable=True),
        sa.Column("food_preferences", sa.String(), nullable=True),
        sa.Column("dietary_restrictions", sa.String(), nullable=True),
        sa.Column("personality_notes", sa.String(), nullable=True),
        sa.Column("communication_style_term_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["communication_style_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index(
        "ix_person_personality_person_id", "person_personality", ["person_id"]
    )

    # ── person_life_event ─────────────────────────────────────────────────────
    op.create_table(
        "person_life_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("event_type_term_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("occurred_year", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_type_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_person_life_event_person_id", "person_life_event", ["person_id"]
    )
    op.create_index(
        "ix_person_life_event_owner_id", "person_life_event", ["owner_id"]
    )

    # ── person_significant_date ───────────────────────────────────────────────
    op.create_table(
        "person_significant_date",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column(
            "recurs_annually", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_person_significant_date_person_id",
        "person_significant_date",
        ["person_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_person_significant_date_person_id", table_name="person_significant_date"
    )
    op.drop_table("person_significant_date")

    op.drop_index("ix_person_life_event_owner_id", table_name="person_life_event")
    op.drop_index("ix_person_life_event_person_id", table_name="person_life_event")
    op.drop_table("person_life_event")

    op.drop_index("ix_person_personality_person_id", table_name="person_personality")
    op.drop_table("person_personality")

    op.drop_index("ix_person_physical_person_id", table_name="person_physical")
    op.drop_table("person_physical")

    op.drop_column("person_social", "telegram_handle")
    op.drop_column("person_social", "discord_handle")
    op.drop_column("person_social", "github_handle")
    op.drop_column("person_social", "facebook_url")

    op.drop_constraint(
        "fk_person_context_preferred_contact_term", "person_context", type_="foreignkey"
    )
    op.drop_column("person_context", "preferred_contact_term_id")
    op.drop_column("person_context", "contact_frequency_days")
    op.drop_column("person_context", "last_contacted_on")
