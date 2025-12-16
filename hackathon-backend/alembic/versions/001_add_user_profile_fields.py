"""Add bio and location to users table

Revision ID: 001
Revises: 
Create Date: 2025-12-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bio and location columns to users table."""
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove bio and location columns from users table."""
    op.drop_column('users', 'location')
    op.drop_column('users', 'bio')

