"""relationship inverse_id and term reverse_slug

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("term", sa.Column("reverse_slug", sa.String(), nullable=True))
    op.add_column(
        "person_relationship",
        sa.Column("inverse_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_person_relationship_inverse_id",
        "person_relationship",
        "person_relationship",
        ["inverse_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_person_relationship_inverse_id", "person_relationship", type_="foreignkey"
    )
    op.drop_column("person_relationship", "inverse_id")
    op.drop_column("term", "reverse_slug")
