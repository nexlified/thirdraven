"""structured addresses and contact methods

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create person_contact_method table ──────────────────────────────────
    op.create_table(
        "person_contact_method",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_person_contact_method_person_id"),
        "person_contact_method",
        ["person_id"],
        unique=False,
    )

    # ── 2. Migrate existing email/phone → person_contact_method ───────────────
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, owner_id, email, phone FROM person WHERE email IS NOT NULL OR phone IS NOT NULL")
    ).fetchall()
    for row in rows:
        person_id, owner_id, email, phone = row
        if email:
            connection.execute(
                sa.text(
                    "INSERT INTO person_contact_method (id, person_id, owner_id, value, type, is_primary, created_at) "
                    "VALUES (gen_random_uuid(), :pid, :oid, :val, 'email', true, now())"
                ),
                {"pid": person_id, "oid": owner_id, "val": email},
            )
        if phone:
            connection.execute(
                sa.text(
                    "INSERT INTO person_contact_method (id, person_id, owner_id, value, type, is_primary, created_at) "
                    "VALUES (gen_random_uuid(), :pid, :oid, :val, 'phone', true, now())"
                ),
                {"pid": person_id, "oid": owner_id, "val": phone},
            )

    # ── 3. Add new address columns to person_location ─────────────────────────
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
    op.create_foreign_key(
        "fk_person_location_home_country_id",
        "person_location", "country",
        ["home_country_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_person_location_work_country_id",
        "person_location", "country",
        ["work_country_id"], ["id"],
    )

    # ── 4. Migrate old address/city/country → new columns ────────────────────
    op.execute(
        sa.text(
            "UPDATE person_location SET "
            "home_street = address_home, "
            "home_city = city, "
            "home_country_id = country_id, "
            "work_street = address_work"
        )
    )

    # ── 5. Drop old columns from person (email, phone) ────────────────────────
    op.drop_column("person", "email")
    op.drop_column("person", "phone")

    # ── 6. Drop old columns from person_location ─────────────────────────────
    op.drop_constraint("person_location_country_id_fkey", "person_location", type_="foreignkey")
    op.drop_column("person_location", "address_home")
    op.drop_column("person_location", "address_work")
    op.drop_column("person_location", "city")
    op.drop_column("person_location", "country_id")


def downgrade() -> None:
    # ── Re-add old person_location columns ────────────────────────────────────
    op.add_column("person_location", sa.Column("address_home", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("address_work", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("city", sa.String(), nullable=True))
    op.add_column("person_location", sa.Column("country_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "person_location_country_id_fkey",
        "person_location", "country",
        ["country_id"], ["id"],
    )

    # Migrate data back
    op.execute(
        sa.text(
            "UPDATE person_location SET "
            "address_home = home_street, "
            "city = home_city, "
            "country_id = home_country_id, "
            "address_work = work_street"
        )
    )

    # Drop new address columns
    op.drop_constraint("fk_person_location_home_country_id", "person_location", type_="foreignkey")
    op.drop_constraint("fk_person_location_work_country_id", "person_location", type_="foreignkey")
    for col in [
        "home_street", "home_city", "home_postal_code", "home_country_id", "home_lat", "home_lng",
        "work_street", "work_city", "work_postal_code", "work_country_id", "work_lat", "work_lng",
    ]:
        op.drop_column("person_location", col)

    # ── Re-add email/phone to person ─────────────────────────────────────────
    op.add_column("person", sa.Column("email", sa.String(), nullable=True))
    op.add_column("person", sa.Column("phone", sa.String(), nullable=True))

    # Migrate primary contacts back
    connection = op.get_bind()
    emails = connection.execute(
        sa.text(
            "SELECT person_id, value FROM person_contact_method "
            "WHERE type = 'email' AND is_primary = true"
        )
    ).fetchall()
    for person_id, value in emails:
        connection.execute(
            sa.text("UPDATE person SET email = :val WHERE id = :pid"),
            {"val": value, "pid": person_id},
        )
    phones = connection.execute(
        sa.text(
            "SELECT person_id, value FROM person_contact_method "
            "WHERE type = 'phone' AND is_primary = true"
        )
    ).fetchall()
    for person_id, value in phones:
        connection.execute(
            sa.text("UPDATE person SET phone = :val WHERE id = :pid"),
            {"val": value, "pid": person_id},
        )

    # ── Drop person_contact_method table ─────────────────────────────────────
    op.drop_index(
        op.f("ix_person_contact_method_person_id"), table_name="person_contact_method"
    )
    op.drop_table("person_contact_method")
