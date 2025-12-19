"""Add item_embeddings table (optional - for caching embeddings)

Revision ID: 006
Revises: 005
Create Date: 2025-12-17

Note: This table is optional. Embeddings are primarily stored in Pinecone.
This table can be used for local caching/backup if needed.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create item_embeddings table (optional - for caching)
    op.create_table(
        'item_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.BigInteger(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id'),
        sa.ForeignKeyConstraint(['item_id'], ['mercari_items.item_id'], ondelete='CASCADE')
    )
    op.create_index('idx_item_id', 'item_embeddings', ['item_id'])


def downgrade():
    op.drop_index('idx_item_id', table_name='item_embeddings')
    op.drop_table('item_embeddings')

