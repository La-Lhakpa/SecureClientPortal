"""remove roles and change to sender/receiver model

Revision ID: 0004_remove_roles_sender_receiver
Revises: 0003_add_username
Create Date: 2026-01-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_remove_roles_sender_receiver"
down_revision = "0003_add_username"
branch_labels = None
depends_on = None


def upgrade():
    # Remove role column from users table
    with op.batch_alter_table("users", schema=None) as batch_op:
        # Check if role column exists before dropping
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'role' in columns:
            batch_op.drop_column("role")
        # Remove username column if it exists
        if 'username' in columns:
            batch_op.drop_column("username")
    
    # Update files table: owner_id -> sender_id, client_id -> receiver_id
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    file_columns = [col['name'] for col in inspector.get_columns('files')]
    
    # Handle client_id NULL values BEFORE renaming (using original column names)
    if 'client_id' in file_columns:
        # For existing NULL client_id, set to owner_id
        if 'owner_id' in file_columns:
            op.execute("""
                UPDATE files 
                SET client_id = owner_id 
                WHERE client_id IS NULL AND owner_id IS NOT NULL
            """)
        elif 'sender_id' in file_columns:
            op.execute("""
                UPDATE files 
                SET client_id = sender_id 
                WHERE client_id IS NULL AND sender_id IS NOT NULL
            """)
    
    # Now do the renames
    with op.batch_alter_table("files", schema=None) as batch_op:
        # Rename owner_id to sender_id if it exists
        if 'owner_id' in file_columns and 'sender_id' not in file_columns:
            batch_op.alter_column("owner_id", new_column_name="sender_id", existing_type=sa.Integer(), nullable=False)
        
        # Rename client_id to receiver_id and make it required
        if 'client_id' in file_columns:
            batch_op.alter_column("client_id", new_column_name="receiver_id", existing_type=sa.Integer(), nullable=False)
        elif 'receiver_id' not in file_columns:
            # If receiver_id doesn't exist, create it (shouldn't happen, but safety check)
            source_col = 'sender_id' if 'sender_id' in file_columns else 'owner_id'
            if source_col == 'sender_id':
                op.execute("""
                    ALTER TABLE files 
                    ADD COLUMN receiver_id INTEGER NOT NULL DEFAULT 1
                """)
                op.execute("""
                    UPDATE files 
                    SET receiver_id = sender_id 
                    WHERE receiver_id = 1
                """)
            else:
                op.execute("""
                    ALTER TABLE files 
                    ADD COLUMN receiver_id INTEGER NOT NULL DEFAULT 1
                """)
                op.execute("""
                    UPDATE files 
                    SET receiver_id = owner_id 
                    WHERE receiver_id = 1
                """)
            op.execute("""
                ALTER TABLE files 
                ALTER COLUMN receiver_id DROP DEFAULT
            """)


def downgrade():
    # Revert files table changes
    with op.batch_alter_table("files", schema=None) as batch_op:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        file_columns = [col['name'] for col in inspector.get_columns('files')]
        
        if 'sender_id' in file_columns and 'owner_id' not in file_columns:
            batch_op.alter_column("sender_id", new_column_name="owner_id", existing_type=sa.Integer(), nullable=False)
        
        if 'receiver_id' in file_columns:
            batch_op.alter_column("receiver_id", new_column_name="client_id", existing_type=sa.Integer(), nullable=True)
    
    # Re-add role column to users
    with op.batch_alter_table("users", schema=None) as batch_op:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'role' not in columns:
            batch_op.add_column(sa.Column("role", sa.String(), nullable=False, server_default="CLIENT"))
