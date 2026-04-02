"""fix_support_knowledge_enum

Revision ID: fb79dda5d643
Revises: ed244f9f3d90
Create Date: 2026-04-02 16:30:00.802674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb79dda5d643'
down_revision: Union[str, Sequence[str], None] = 'ed244f9f3d90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the Enum type
    op.execute("CREATE TYPE supportknowledgecategory AS ENUM ('GENERAL', 'POLICY', 'SHIPPING', 'PRODUCT', 'PROMO')")
    
    # Alter the column to use the new Enum type with explicit casting
    op.execute("ALTER TABLE support_knowledge ALTER COLUMN category TYPE supportknowledgecategory USING category::supportknowledgecategory")
    
    # Set default value
    op.execute("ALTER TABLE support_knowledge ALTER COLUMN category SET DEFAULT 'GENERAL'")


def downgrade() -> None:
    """Downgrade schema."""
    # Convert back to VARCHAR
    op.execute("ALTER TABLE support_knowledge ALTER COLUMN category TYPE VARCHAR(100) USING category::VARCHAR")
    
    # Drop the Enum type
    op.execute("DROP TYPE supportknowledgecategory")
