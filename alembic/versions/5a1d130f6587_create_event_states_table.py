"""create event states table

Revision ID: 5a1d130f6587
Revises: 
Create Date: 2026-10-08 21:07:36.870719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a1d130f6587'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "event_states",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("info", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("timestamp", sa.String(), nullable=False),
        sa.Column("publish_timestamp", sa.String(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("threat_level_id", sa.String(), nullable=False),
        sa.Column("analysis", sa.String(), nullable=False),
        sa.Column("attribute_count", sa.Integer(), nullable=False),
        sa.Column("object_count", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("tag_names", sa.JSON(), nullable=False),
        sa.Column("galaxy_tag_names", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("event_states")
