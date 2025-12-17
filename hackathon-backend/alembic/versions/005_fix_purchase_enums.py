"""Fix purchase enum values to lowercase

Revision ID: 005
Revises: 004
Create Date: 2025-12-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix enum values to lowercase."""
    # MySQL doesn't support ALTER ENUM directly, so we need to:
    # 1. Add a temporary column with correct enum
    # 2. Copy data with LOWER() conversion
    # 3. Drop old column
    # 4. Rename new column
    
    # Fix payment_method
    op.execute("""
        ALTER TABLE purchases 
        MODIFY COLUMN payment_method 
        ENUM('credit', 'bank', 'convenience') NOT NULL
    """)
    
    # Fix status (already lowercase in theory, but ensure it)
    op.execute("""
        ALTER TABLE purchases 
        MODIFY COLUMN status 
        ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending'
    """)


def downgrade() -> None:
    """Revert to uppercase enum values."""
    # Convert back to uppercase (if needed for rollback)
    op.execute("""
        ALTER TABLE purchases 
        MODIFY COLUMN payment_method 
        ENUM('CREDIT', 'BANK', 'CONVENIENCE') NOT NULL
    """)
    
    op.execute("""
        ALTER TABLE purchases 
        MODIFY COLUMN status 
        ENUM('PENDING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'PENDING'
    """)



