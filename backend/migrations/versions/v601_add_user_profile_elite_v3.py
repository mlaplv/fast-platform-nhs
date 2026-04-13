"""Elite V3.0: Add user profile columns (gender, dob, avatar_url, extra_metadata)

Revision ID: v601_add_user_profile_elite_v3
Revises: v600_neural_media_linker
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = 'v601_add_user_profile_elite_v3'
down_revision = ('v600_neural_media_linker', 'c8d9e1f2a3b4')
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('users')]

    if 'gender' not in existing_columns:
        op.add_column('users', sa.Column('gender', sa.String(), nullable=True))

    if 'dob' not in existing_columns:
        op.add_column('users', sa.Column('dob', sa.DateTime(timezone=True), nullable=True))

    if 'avatar_url' not in existing_columns:
        op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))

    if 'extra_metadata' not in existing_columns:
        op.add_column('users', sa.Column('extra_metadata', sa.JSON(), nullable=True, server_default=sa.text("'{}'")))


def downgrade() -> None:
    op.drop_column('users', 'extra_metadata')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'dob')
    op.drop_column('users', 'gender')
