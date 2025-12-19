"""Add image_url column to item_listings table

Revision ID: 007
Revises: 006
Create Date: 2025-12-17

Adds image_url column to store Supabase Storage URLs for item images.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add image_url column to item_listings table
    op.add_column('item_listings', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade():
    # Remove image_url column from item_listings table
    op.drop_column('item_listings', 'image_url')

