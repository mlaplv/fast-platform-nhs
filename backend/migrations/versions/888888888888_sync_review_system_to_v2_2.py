"""sync review system to v2.2

Revision ID: 888888888888
Revises: 4295a9108a27
Create Date: 2026-04-29 05:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '888888888888'
down_revision: Union[str, None] = 'f271e83172cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add CATEGORY to ReviewEntityType enum
    # We use execute because ALTER TYPE cannot be run inside a transaction in some Postgres versions, 
    # but Alembic usually handles this or we can use op.execute
    op.execute("ALTER TYPE reviewentitytype ADD VALUE IF NOT EXISTS 'CATEGORY'")
    
    # 2. Cast columns to JSONB
    op.execute("ALTER TABLE system_reviews ALTER COLUMN attributes TYPE JSONB USING attributes::jsonb")
    op.execute("ALTER TABLE system_reviews ALTER COLUMN attachments TYPE JSONB USING attachments::jsonb")

def downgrade() -> None:
    # Reverse casting (optional, but good practice)
    op.execute("ALTER TABLE system_reviews ALTER COLUMN attributes TYPE JSON USING attributes::json")
    op.execute("ALTER TABLE system_reviews ALTER COLUMN attachments TYPE JSON USING attachments::json")
    # Note: Removing a value from an Enum is complex in Postgres and usually not recommended in migrations.
