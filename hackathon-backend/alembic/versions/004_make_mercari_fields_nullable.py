"""Make mercari_items fields nullable for item creation

Revision ID: 004
Revises: 003
Create Date: 2025-12-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Make fields nullable
    op.alter_column('mercari_items', 'user_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('mercari_items', 'stime', existing_type=sa.DateTime(), nullable=True)
    op.alter_column('mercari_items', 'session_id', existing_type=sa.String(255), nullable=True)
    op.alter_column('mercari_items', 'sequence_id', existing_type=sa.String(100), nullable=True)
    op.alter_column('mercari_items', 'sequence_length', existing_type=sa.Integer(), nullable=True)
    op.alter_column('mercari_items', 'event_id', existing_type=sa.String(50), nullable=True)


def downgrade():
    # Revert to NOT NULL
    op.alter_column('mercari_items', 'user_id', existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('mercari_items', 'stime', existing_type=sa.DateTime(), nullable=False)
    op.alter_column('mercari_items', 'session_id', existing_type=sa.String(255), nullable=False)
    op.alter_column('mercari_items', 'sequence_id', existing_type=sa.String(100), nullable=False)
    op.alter_column('mercari_items', 'sequence_length', existing_type=sa.Integer(), nullable=False)
    op.alter_column('mercari_items', 'event_id', existing_type=sa.String(50), nullable=False)




