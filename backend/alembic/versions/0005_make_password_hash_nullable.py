"""make password_hash nullable for google users

Revision ID: 0005_make_password_hash_nullable
Revises: 0004_remove_roles_sender_receiver
Create Date: 2026-01-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_make_password_hash_nullable"
down_revision = "0004_remove_roles_sender_receiver"
branch_labels = None
depends_on = None


def upgrade():
    # Make password_hash nullable to support Google OAuth users
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "password_hash",
            existing_type=sa.String(),
            nullable=True,
        )


def downgrade():
    # Revert password_hash to NOT NULL (requires setting default for existing NULL values)
    with op.batch_alter_table("users", schema=None) as batch_op:
        # Set empty string for NULL password_hash values before making it NOT NULL
        op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
        batch_op.alter_column(
            "password_hash",
            existing_type=sa.String(),
            nullable=False,
        )
