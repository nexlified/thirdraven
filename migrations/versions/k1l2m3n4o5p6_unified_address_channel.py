"""unified address and channel tables

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-03-27

Replaces:
  - person_contact_method  →  person_channel  (+ social handles + linkedin + phone_secondary)
  - person_social          →  person_channel rows
  - person_location address columns  →  person_address rows
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create person_channel ───────────────────────────────────────────────
    op.create_table(
        "person_channel",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_channel_person_id", "person_channel", ["person_id"])

    # ── 2. Create person_address ───────────────────────────────────────────────
    op.create_table(
        "person_address",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="home"),
        sa.Column("street", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("postal_code", sa.String(), nullable=True),
        sa.Column("country_id", sa.Uuid(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["country_id"], ["country.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_address_person_id", "person_address", ["person_id"])

    # ── 3. Migrate person_contact_method → person_channel ─────────────────────
    op.execute("""
        INSERT INTO person_channel (id, person_id, owner_id, type, value, label, is_primary, created_at)
        SELECT id, person_id, owner_id, type, value, label, is_primary, created_at
        FROM person_contact_method
    """)

    # ── 4. Migrate person_social → person_channel ─────────────────────────────
    _social_fields = [
        ("twitter_handle",   "twitter"),
        ("instagram_handle", "instagram"),
        ("website_url",      "website"),
        ("facebook_url",     "facebook"),
        ("github_handle",    "github"),
        ("discord_handle",   "discord"),
        ("telegram_handle",  "telegram"),
    ]
    for col, ch_type in _social_fields:
        op.execute(f"""
            INSERT INTO person_channel (id, person_id, owner_id, type, value, is_primary, created_at)
            SELECT
                gen_random_uuid(),
                ps.person_id,
                p.owner_id,
                '{ch_type}',
                ps.{col},
                false,
                NOW()
            FROM person_social ps
            JOIN person p ON p.id = ps.person_id
            WHERE ps.{col} IS NOT NULL
        """)

    # ── 5. Migrate person_professional.linkedin_url → person_channel ──────────
    op.execute("""
        INSERT INTO person_channel (id, person_id, owner_id, type, value, is_primary, created_at)
        SELECT
            gen_random_uuid(),
            pp.person_id,
            p.owner_id,
            'linkedin',
            pp.linkedin_url,
            false,
            NOW()
        FROM person_professional pp
        JOIN person p ON p.id = pp.person_id
        WHERE pp.linkedin_url IS NOT NULL
    """)

    # ── 6. Migrate person_professional.phone_secondary → person_channel ───────
    op.execute("""
        INSERT INTO person_channel (id, person_id, owner_id, type, value, is_primary, created_at)
        SELECT
            gen_random_uuid(),
            pp.person_id,
            p.owner_id,
            'phone',
            pp.phone_secondary,
            false,
            NOW()
        FROM person_professional pp
        JOIN person p ON p.id = pp.person_id
        WHERE pp.phone_secondary IS NOT NULL
    """)

    # ── 7. Migrate person_location addresses → person_address ─────────────────
    op.execute("""
        INSERT INTO person_address (id, person_id, owner_id, type, street, city, postal_code, country_id, lat, lng, is_primary, created_at)
        SELECT
            gen_random_uuid(),
            pl.person_id,
            p.owner_id,
            'home',
            pl.home_street,
            pl.home_city,
            pl.home_postal_code,
            pl.home_country_id,
            pl.home_lat,
            pl.home_lng,
            true,
            NOW()
        FROM person_location pl
        JOIN person p ON p.id = pl.person_id
        WHERE COALESCE(pl.home_street, pl.home_city, pl.home_postal_code) IS NOT NULL
           OR pl.home_country_id IS NOT NULL
           OR pl.home_lat IS NOT NULL
    """)

    op.execute("""
        INSERT INTO person_address (id, person_id, owner_id, type, street, city, postal_code, country_id, lat, lng, is_primary, created_at)
        SELECT
            gen_random_uuid(),
            pl.person_id,
            p.owner_id,
            'work',
            pl.work_street,
            pl.work_city,
            pl.work_postal_code,
            pl.work_country_id,
            pl.work_lat,
            pl.work_lng,
            false,
            NOW()
        FROM person_location pl
        JOIN person p ON p.id = pl.person_id
        WHERE COALESCE(pl.work_street, pl.work_city, pl.work_postal_code) IS NOT NULL
           OR pl.work_country_id IS NOT NULL
           OR pl.work_lat IS NOT NULL
    """)

    # ── 8. Drop person_contact_method ─────────────────────────────────────────
    op.drop_table("person_contact_method")

    # ── 9. Drop person_social ─────────────────────────────────────────────────
    op.drop_table("person_social")

    # ── 10. Drop linkedin_url, phone_secondary from person_professional ────────
    op.drop_column("person_professional", "linkedin_url")
    op.drop_column("person_professional", "phone_secondary")

    # ── 11. Drop address columns from person_location ─────────────────────────
    for col in (
        "home_street", "home_city", "home_postal_code",
        "home_country_id", "home_lat", "home_lng",
        "work_street", "work_city", "work_postal_code",
        "work_country_id", "work_lat", "work_lng",
    ):
        op.drop_column("person_location", col)


def downgrade() -> None:
    # ── Restore address columns on person_location ────────────────────────────
    op.add_column("person_location", sa.Column("home_street", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("home_city", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("home_postal_code", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("home_country_id", sa.Uuid(), nullable=True))
    op.add_column("person_location", sa.Column("home_lat", sa.Float(), nullable=True))
    op.add_column("person_location", sa.Column("home_lng", sa.Float(), nullable=True))
    op.add_column("person_location", sa.Column("work_street", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("work_city", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("work_postal_code", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("work_country_id", sa.Uuid(), nullable=True))
    op.add_column("person_location", sa.Column("work_lat", sa.Float(), nullable=True))
    op.add_column("person_location", sa.Column("work_lng", sa.Float(), nullable=True))

    # ── Restore person_professional columns ───────────────────────────────────
    op.add_column("person_professional", sa.Column("linkedin_url", sa.String(), nullable=True))
    op.add_column("person_professional", sa.Column("phone_secondary", sa.String(), nullable=True))

    # ── Restore person_social ─────────────────────────────────────────────────
    op.create_table(
        "person_social",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("twitter_handle", sa.String(), nullable=True),
        sa.Column("instagram_handle", sa.String(), nullable=True),
        sa.Column("website_url", sa.String(), nullable=True),
        sa.Column("facebook_url", sa.String(), nullable=True),
        sa.Column("github_handle", sa.String(), nullable=True),
        sa.Column("discord_handle", sa.String(), nullable=True),
        sa.Column("telegram_handle", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id"),
    )

    # ── Restore person_contact_method ─────────────────────────────────────────
    op.create_table(
        "person_contact_method",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Migrate email/phone channels back to person_contact_method
    op.execute("""
        INSERT INTO person_contact_method (id, person_id, owner_id, type, value, label, is_primary, created_at)
        SELECT id, person_id, owner_id, type, value, label, is_primary, created_at
        FROM person_channel
        WHERE type IN ('email', 'mobile', 'phone', 'whatsapp', 'telegram')
    """)

    # ── Drop new tables ───────────────────────────────────────────────────────
    op.drop_index("ix_person_address_person_id", table_name="person_address")
    op.drop_table("person_address")
    op.drop_index("ix_person_channel_person_id", table_name="person_channel")
    op.drop_table("person_channel")
