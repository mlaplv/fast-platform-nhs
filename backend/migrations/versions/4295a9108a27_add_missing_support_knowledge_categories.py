"""add_missing_support_knowledge_categories

Revision ID: 4295a9108a27
Revises: 42777f61da1a
Create Date: 2026-04-08 09:50:05.772424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4295a9108a27'
down_revision: Union[str, Sequence[str], None] = '42777f61da1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new values to the enum
    op.execute("ALTER TYPE supportknowledgecategory ADD VALUE IF NOT EXISTS 'INFO_ADDRESS'")
    op.execute("ALTER TYPE supportknowledgecategory ADD VALUE IF NOT EXISTS 'INFO_HOTLINE'")
    op.execute("ALTER TYPE supportknowledgecategory ADD VALUE IF NOT EXISTS 'INFO_INGREDIENTS'")
    op.execute("ALTER TYPE supportknowledgecategory ADD VALUE IF NOT EXISTS 'PRICE_QUERY'")
    op.execute("ALTER TYPE supportknowledgecategory ADD VALUE IF NOT EXISTS 'INFO_SHIPPING'")


def downgrade() -> None:
    """Downgrade schema - Removing enum values is not supported in Postgres."""
    pass
