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
    # ── user ──────────────────────────────────────────────────────────────────
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

    # ── country ───────────────────────────────────────────────────────────────
    op.create_table(
        "country",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("alpha2", sa.String(), nullable=False),
        sa.Column("alpha3", sa.String(), nullable=False),
        sa.Column("numeric", sa.String(), nullable=False),
        sa.Column("calling_code", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("subregion", sa.String(), nullable=True),
        sa.Column("flag_emoji", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alpha2"),
        sa.UniqueConstraint("alpha3"),
    )
    op.create_index("ix_country_alpha2", "country", ["alpha2"])
    op.create_index("ix_country_alpha3", "country", ["alpha3"])

    # ── language ──────────────────────────────────────────────────────────────
    op.create_table(
        "language",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("native_name", sa.String(), nullable=False),
        sa.Column("iso_639_1", sa.String(), nullable=False),
        sa.Column("iso_639_2", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iso_639_1"),
        sa.UniqueConstraint("iso_639_2"),
    )
    op.create_index("ix_language_iso_639_1", "language", ["iso_639_1"])
    op.create_index("ix_language_iso_639_2", "language", ["iso_639_2"])

    # ── vocabulary ────────────────────────────────────────────────────────────
    op.create_table(
        "vocabulary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("machine_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "is_hierarchical", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "allows_new_terms", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "source_type", sa.String(), nullable=False, server_default="internal"
        ),
        sa.Column("external_provider", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("machine_name"),
    )
    op.create_index("ix_vocabulary_machine_name", "vocabulary", ["machine_name"])

    # ── term ──────────────────────────────────────────────────────────────────
    op.create_table(
        "term",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vocabulary_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["vocabulary_id"], ["vocabulary.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vocabulary_id", "slug"),
    )
    op.create_index("ix_term_vocabulary_id", "term", ["vocabulary_id"])
    op.create_index("ix_term_slug", "term", ["slug"])

    # ── timezone ──────────────────────────────────────────────────────────────
    op.create_table(
        "timezone",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("utc_offset", sa.String(), nullable=False),
        sa.Column("utc_offset_dst", sa.String(), nullable=True),
        sa.Column("country_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["country_id"], ["country.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_timezone_name", "timezone", ["name"])

    # ── person (slim core) ────────────────────────────────────────────────────
    op.create_table(
        "person",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("closeness_level", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_owner_id", "person", ["owner_id"])

    # ── person_relationship ────────────────────────────────────────────────────
    op.create_table(
        "person_relationship",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("from_person_id", sa.Uuid(), nullable=False),
        sa.Column("to_person_id", sa.Uuid(), nullable=False),
        sa.Column("label_term_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["from_person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["label_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["to_person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_person_relationship_from_person_id",
        "person_relationship",
        ["from_person_id"],
    )
    op.create_index(
        "ix_person_relationship_to_person_id",
        "person_relationship",
        ["to_person_id"],
    )

    # ── person_profile ─────────────────────────────────────────────────────────
    op.create_table(
        "person_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("middle_name", sa.String(), nullable=True),
        sa.Column("prefix_term_id", sa.Uuid(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender_term_id", sa.Uuid(), nullable=True),
        sa.Column("nationality_country_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["gender_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["nationality_country_id"], ["country.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["prefix_term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index("ix_person_profile_person_id", "person_profile", ["person_id"])

    # ── person_professional ────────────────────────────────────────────────────
    op.create_table(
        "person_professional",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("occupation_term_id", sa.Uuid(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("job_title", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("phone_secondary", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["occupation_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index(
        "ix_person_professional_person_id", "person_professional", ["person_id"]
    )

    # ── person_social ──────────────────────────────────────────────────────────
    op.create_table(
        "person_social",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("twitter_handle", sa.String(), nullable=True),
        sa.Column("instagram_handle", sa.String(), nullable=True),
        sa.Column("website_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index("ix_person_social_person_id", "person_social", ["person_id"])

    # ── person_location ────────────────────────────────────────────────────────
    op.create_table(
        "person_location",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("address_home", sa.String(), nullable=True),
        sa.Column("address_work", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("country_id", sa.Uuid(), nullable=True),
        sa.Column("timezone_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["country.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["timezone_id"], ["timezone.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index("ix_person_location_person_id", "person_location", ["person_id"])

    # ── person_context ─────────────────────────────────────────────────────────
    op.create_table(
        "person_context",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("how_we_met", sa.String(), nullable=True),
        sa.Column("first_met_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )
    op.create_index("ix_person_context_person_id", "person_context", ["person_id"])

    # ── person_tag ─────────────────────────────────────────────────────────────
    op.create_table(
        "person_tag",
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("person_id", "term_id"),
    )

    # ── person_language ────────────────────────────────────────────────────────
    op.create_table(
        "person_language",
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("language_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("person_id", "language_id"),
    )

    # ── person_term ────────────────────────────────────────────────────────────
    op.create_table(
        "person_term",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("context", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_term_person_id", "person_term", ["person_id"])
    op.create_index("ix_person_term_term_id", "person_term", ["term_id"])

    # ── asset ──────────────────────────────────────────────────────────────────
    op.create_table(
        "asset",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category_term_id", sa.Uuid(), nullable=False),
        sa.Column("status_term_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("serial_number", sa.String(), nullable=True),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_price", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["status_term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_owner_id", "asset", ["owner_id"])

    # ── asset_tag ──────────────────────────────────────────────────────────────
    op.create_table(
        "asset_tag",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("asset_id", "term_id"),
    )

    # ── interaction ────────────────────────────────────────────────────────────
    op.create_table(
        "interaction",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("interaction_type_id", sa.Uuid(), nullable=True),
        sa.Column("term_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["interaction_type_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interaction_person_id", "interaction", ["person_id"])
    op.create_index("ix_interaction_owner_id", "interaction", ["owner_id"])

    # ── contact (legacy, unchanged) ────────────────────────────────────────────
    op.create_table(
        "contact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=True),
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
    op.drop_index(
        "ix_contact_relationship_to_contact_id", table_name="contact_relationship"
    )
    op.drop_index(
        "ix_contact_relationship_from_contact_id", table_name="contact_relationship"
    )
    op.drop_table("contact_relationship")
    op.drop_index("ix_contact_owner_id", table_name="contact")
    op.drop_table("contact")

    op.drop_index("ix_interaction_owner_id", table_name="interaction")
    op.drop_index("ix_interaction_person_id", table_name="interaction")
    op.drop_table("interaction")

    op.drop_table("asset_tag")
    op.drop_index("ix_asset_owner_id", table_name="asset")
    op.drop_table("asset")

    op.drop_index("ix_person_term_term_id", table_name="person_term")
    op.drop_index("ix_person_term_person_id", table_name="person_term")
    op.drop_table("person_term")
    op.drop_table("person_language")
    op.drop_table("person_tag")
    op.drop_index("ix_person_context_person_id", table_name="person_context")
    op.drop_table("person_context")
    op.drop_index("ix_person_location_person_id", table_name="person_location")
    op.drop_table("person_location")
    op.drop_index("ix_person_social_person_id", table_name="person_social")
    op.drop_table("person_social")
    op.drop_index("ix_person_professional_person_id", table_name="person_professional")
    op.drop_table("person_professional")
    op.drop_index("ix_person_profile_person_id", table_name="person_profile")
    op.drop_table("person_profile")
    op.drop_index(
        "ix_person_relationship_to_person_id", table_name="person_relationship"
    )
    op.drop_index(
        "ix_person_relationship_from_person_id", table_name="person_relationship"
    )
    op.drop_table("person_relationship")
    op.drop_index("ix_person_owner_id", table_name="person")
    op.drop_table("person")

    op.drop_index("ix_timezone_name", table_name="timezone")
    op.drop_table("timezone")

    op.drop_index("ix_term_slug", table_name="term")
    op.drop_index("ix_term_vocabulary_id", table_name="term")
    op.drop_table("term")

    op.drop_index("ix_vocabulary_machine_name", table_name="vocabulary")
    op.drop_table("vocabulary")

    op.drop_index("ix_language_iso_639_2", table_name="language")
    op.drop_index("ix_language_iso_639_1", table_name="language")
    op.drop_table("language")

    op.drop_index("ix_country_alpha3", table_name="country")
    op.drop_index("ix_country_alpha2", table_name="country")
    op.drop_table("country")

    op.drop_index("ix_user_email", table_name="user")
    op.drop_index("ix_user_username", table_name="user")
    op.drop_table("user")
