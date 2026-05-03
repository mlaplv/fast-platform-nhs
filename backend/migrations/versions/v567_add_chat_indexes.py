"""add_chat_composite_indexes — NEUTRALIZED (superseded by 386bdee21636)

[Elite V2.2] Các indexes cũ dạng DESC expression đã được thay thế hoàn toàn
bởi migration 386bdee21636 (ix_chat_user_time, ix_chat_session_time, ix_chat_deleted_at).
Cú pháp sa.text('created_at DESC') không tương thích PostgreSQL 16 + asyncpg.
Chain được giữ nguyên (revision/down_revision không đổi).

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
    # [NEUTRALIZED] Superseded by migration 386bdee21636_add_chat_message_indexes.
    # Indexes (ix_chat_user_time, ix_chat_session_time, ix_chat_deleted_at) are
    # created by the authoritative migration at the end of the chain.
    pass


def downgrade() -> None:
    # [NEUTRALIZED] Nothing to drop.
    pass
