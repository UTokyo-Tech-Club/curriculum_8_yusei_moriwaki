"""Add description to mercari_items

Revision ID: 003
Revises: 002
Create Date: 2025-12-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mercari_items', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('mercari_items', 'description')

