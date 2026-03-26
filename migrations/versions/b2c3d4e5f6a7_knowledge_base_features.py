"""knowledge_base: observations, organizations, follow-ups, goals, events

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── person_observation ────────────────────────────────────────────────────
    op.create_table(
        "person_observation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_observation_person_id", "person_observation", ["person_id"])
    op.create_index("ix_person_observation_owner_id", "person_observation", ["owner_id"])

    # ── person_observation_tag ─────────────────────────────────────────────────
    op.create_table(
        "person_observation_tag",
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["observation_id"], ["person_observation.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("observation_id", "term_id"),
    )

    # ── organization ──────────────────────────────────────────────────────────
    op.create_table(
        "organization",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type_term_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("industry_term_id", sa.Uuid(), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("headquarters_city", sa.String(), nullable=True),
        sa.Column("country_id", sa.Uuid(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["country.id"]),
        sa.ForeignKeyConstraint(["industry_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["type_term_id"], ["term.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_owner_id", "organization", ["owner_id"])

    # ── person_organization ───────────────────────────────────────────────────
    op.create_table(
        "person_organization",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_person_organization_person_id", "person_organization", ["person_id"]
    )

    # ── person_followup ───────────────────────────────────────────────────────
    op.create_table(
        "person_followup",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("interaction_id", sa.Uuid(), nullable=True),
        sa.Column("cleared_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interaction.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_followup_person_id", "person_followup", ["person_id"])
    op.create_index("ix_person_followup_owner_id", "person_followup", ["owner_id"])

    # ── person_goal ───────────────────────────────────────────────────────────
    op.create_table(
        "person_goal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("goal_type", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("achieved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_goal_person_id", "person_goal", ["person_id"])
    op.create_index("ix_person_goal_owner_id", "person_goal", ["owner_id"])

    # ── event ─────────────────────────────────────────────────────────────────
    op.create_table(
        "event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("event_type_term_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_type_term_id"], ["term.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_owner_id", "event", ["owner_id"])

    # ── event_person ──────────────────────────────────────────────────────────
    op.create_table(
        "event_person",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_person_event_id", "event_person", ["event_id"])
    op.create_index("ix_event_person_person_id", "event_person", ["person_id"])


def downgrade() -> None:
    op.drop_table("event_person")
    op.drop_table("event")
    op.drop_table("person_goal")
    op.drop_table("person_followup")
    op.drop_table("person_organization")
    op.drop_table("organization")
    op.drop_table("person_observation_tag")
    op.drop_table("person_observation")
