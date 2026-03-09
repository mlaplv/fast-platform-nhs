"""add_chat_composite_indexes

Revision ID: v567_add_chat_indexes
Revises: 4b451126979c
Create Date: 2026-03-07 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision = 'v567_add_chat_indexes'
down_revision = '4b451126979c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Composite Index for User History (account tab)
    op.create_index(
        'ix_chat_messages_user_id_created_at_desc',
        'chat_messages',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    # Composite Index for Session History (widget context)
    op.create_index(
        'ix_chat_messages_session_id_created_at_desc',
        'chat_messages',
        ['session_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )

def downgrade() -> None:
    op.drop_index('ix_chat_messages_user_id_created_at_desc', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id_created_at_desc', table_name='chat_messages')
