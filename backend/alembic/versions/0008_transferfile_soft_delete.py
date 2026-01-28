"""transfer_files soft delete per side

Revision ID: 0008_transferfile_soft_delete
Revises: 0007_add_transfers
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_transferfile_soft_delete"
down_revision = "0007_add_transfers"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("transfer_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sender_deleted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("receiver_deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_transfer_files_sender_deleted_at", ["sender_deleted_at"], unique=False)
        batch_op.create_index("ix_transfer_files_receiver_deleted_at", ["receiver_deleted_at"], unique=False)


def downgrade():
    with op.batch_alter_table("transfer_files", schema=None) as batch_op:
        batch_op.drop_index("ix_transfer_files_receiver_deleted_at")
        batch_op.drop_index("ix_transfer_files_sender_deleted_at")
        batch_op.drop_column("receiver_deleted_at")
        batch_op.drop_column("sender_deleted_at")

