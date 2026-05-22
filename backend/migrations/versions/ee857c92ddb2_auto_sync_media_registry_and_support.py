"""auto_sync_media_registry_and_support

Revision ID: ee857c92ddb2
Revises: 7a5bcc5b8068
Create Date: 2026-05-22 13:24:10.401620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee857c92ddb2'
down_revision: Union[str, Sequence[str], None] = '7a5bcc5b8068'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    pass

    # ### end Alembic commands ###
