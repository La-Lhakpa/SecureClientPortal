"""add file metadata fields

Revision ID: 0002_files_metadata
Revises: 0001_init
Create Date: 2026-01-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_files_metadata"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("files") as batch:
        # Rename filename -> original_filename (from initial migration)
        batch.alter_column("filename", new_column_name="original_filename", existing_type=sa.String())
        batch.add_column(sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"))

    # Make original_filename non-null once populated
    op.execute("UPDATE files SET original_filename = '' WHERE original_filename IS NULL")
    with op.batch_alter_table("files") as batch:
        batch.alter_column("original_filename", nullable=False)


def downgrade():
    with op.batch_alter_table("files") as batch:
        batch.alter_column("original_filename", new_column_name="filename", existing_type=sa.String())
        batch.drop_column("size_bytes")
