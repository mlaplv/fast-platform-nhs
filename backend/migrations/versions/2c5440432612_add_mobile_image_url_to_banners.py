"""add_mobile_image_url_to_banners

Revision ID: 2c5440432612
Revises: 386bdee21636
Create Date: 2026-05-05 13:54:51.788167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c5440432612'
down_revision: Union[str, Sequence[str], None] = '386bdee21636'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('banners', sa.Column('mobile_image_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('banners', 'mobile_image_url')
