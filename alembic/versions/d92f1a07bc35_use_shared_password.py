"""Replace accounts with shared-password sessions; invalidate existing sessions."""
from alembic import op
import sqlalchemy as sa

revision = "d92f1a07bc35"
down_revision = "c7b2e91a6d04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("auth_sessions")
    op.drop_table("users")
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("password_version", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.execute(sa.delete(sa.table("auth_throttles")))


def downgrade() -> None:
    # Account data cannot be restored; downgrade recreates only the previous schema.
    op.drop_table("auth_sessions")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
