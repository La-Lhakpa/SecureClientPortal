"""add username to users

Revision ID: 0003_add_username
Revises: 0002_files_metadata
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_username"
down_revision = "0002_files_metadata"
branch_labels = None
depends_on = None


def upgrade():
    # Check if username column already exists (in case database was created manually)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'username' not in columns:
        # Add username column to users table (nullable first)
        op.add_column("users", sa.Column("username", sa.String(), nullable=True))
        
        # Generate usernames from email for existing users
        # Try PostgreSQL syntax first, fallback to SQLite if needed
        try:
            op.execute("""
                UPDATE users 
                SET username = SPLIT_PART(email, '@', 1) || '_' || id::text 
                WHERE username IS NULL
            """)
        except:
            # Fallback for SQLite or other databases
            op.execute("""
                UPDATE users 
                SET username = SUBSTR(email, 1, INSTR(email, '@') - 1) || '_' || id 
                WHERE username IS NULL
            """)
        
        # Make username required
        op.alter_column("users", "username", nullable=False)
        
        # Create unique index
        op.create_index("ix_users_username", "users", ["username"], unique=True)
    else:
        # Column exists, just ensure index exists
        indexes = [idx['name'] for idx in inspector.get_indexes('users')]
        if 'ix_users_username' not in indexes:
            op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_username")
        batch_op.drop_column("username")
