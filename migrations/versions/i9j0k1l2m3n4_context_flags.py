"""context classification flags

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("interaction", sa.Column("context", sa.String(), nullable=True))
    op.add_column("communication", sa.Column("context", sa.String(), nullable=True))
    op.add_column(
        "person_observation", sa.Column("context", sa.String(), nullable=True)
    )
    op.add_column(
        "person_context", sa.Column("relationship_nature", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("person_context", "relationship_nature")
    op.drop_column("person_observation", "context")
    op.drop_column("communication", "context")
    op.drop_column("interaction", "context")
