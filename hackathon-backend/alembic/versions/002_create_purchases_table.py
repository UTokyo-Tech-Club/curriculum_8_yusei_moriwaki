"""Create purchases table

Revision ID: 002
Revises: 001
Create Date: 2025-12-16 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create purchases table."""
    op.create_table(
        'purchases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('buyer_user_id', sa.BigInteger(), nullable=False),
        sa.Column('item_listing_id', sa.Integer(), nullable=False),
        sa.Column('payment_method', sa.Enum('credit', 'bank', 'convenience', name='paymentmethod'), nullable=False),
        sa.Column('shipping_name', sa.String(length=255), nullable=False),
        sa.Column('shipping_postal_code', sa.String(length=20), nullable=False),
        sa.Column('shipping_prefecture', sa.String(length=100), nullable=False),
        sa.Column('shipping_city', sa.String(length=255), nullable=False),
        sa.Column('shipping_address', sa.Text(), nullable=False),
        sa.Column('shipping_building', sa.String(length=255), nullable=True),
        sa.Column('shipping_phone', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'cancelled', name='purchasestatus'), server_default='pending', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['buyer_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_listing_id'], ['item_listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_buyer', 'purchases', ['buyer_user_id'], unique=False)
    op.create_index('idx_status', 'purchases', ['status'], unique=False)


def downgrade() -> None:
    """Drop purchases table."""
    op.drop_index('idx_status', table_name='purchases')
    op.drop_index('idx_buyer', table_name='purchases')
    op.drop_table('purchases')
    
    # Drop the custom enum types (MySQL doesn't need this, but PostgreSQL would)
    # op.execute("DROP TYPE IF EXISTS paymentmethod")
    # op.execute("DROP TYPE IF EXISTS purchasestatus")



