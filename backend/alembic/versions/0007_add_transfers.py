"""add transfers and transfer_files tables

Revision ID: 0007_add_transfers
Revises: 0006_add_file_storage_fields
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_add_transfers"
down_revision = "0006_add_file_storage_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("receiver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("access_code_hash", sa.String(), nullable=False),
        sa.Column("code_hint", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending", index=True),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "transfer_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("stored_filename", sa.String(), nullable=False),
        sa.Column("stored_path", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), index=True),
    )


def downgrade():
    op.drop_table("transfer_files")
    op.drop_table("transfers")

