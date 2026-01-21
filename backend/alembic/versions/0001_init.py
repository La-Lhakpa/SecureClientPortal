"""initial tables

Revision ID: 0001_init
Revises:
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("stored_path", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("files")
    op.drop_table("users")
