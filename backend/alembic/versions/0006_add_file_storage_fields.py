"""add stored_filename and content_type to files

Revision ID: 0006_add_file_storage_fields
Revises: 0005_make_password_hash_nullable
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa
from pathlib import Path


revision = "0006_add_file_storage_fields"
down_revision = "0005_make_password_hash_nullable"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add new columns as nullable first
    with op.batch_alter_table("files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("stored_filename", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("content_type", sa.String(), nullable=True))

    # 2) Backfill stored_filename from stored_path for existing rows
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, stored_path FROM files")).fetchall()
    for row in rows:
        file_id = row[0]
        stored_path = row[1] or ""
        stored_filename = Path(stored_path).name if stored_path else ""
        if not stored_filename:
            # last-resort: keep a placeholder to satisfy NOT NULL
            stored_filename = f"legacy_{file_id}"
        conn.execute(
            sa.text("UPDATE files SET stored_filename = :sf WHERE id = :id"),
            {"sf": stored_filename, "id": file_id},
        )

    # 3) Make stored_filename NOT NULL
    with op.batch_alter_table("files", schema=None) as batch_op:
        batch_op.alter_column("stored_filename", existing_type=sa.String(), nullable=False)


def downgrade():
    with op.batch_alter_table("files", schema=None) as batch_op:
        batch_op.drop_column("content_type")
        batch_op.drop_column("stored_filename")

