"""
Admin Support Inbox Controller — Elite V2.2
============================================
Read-only API for the Admin to view and audit Helen's chat sessions.
All content is decrypted server-side using GeminiSecurity (Zero-Knowledge Inbox).
Follows strictly: 100% static typing, no 'any', Litestar Controller pattern.
"""
from __future__ import annotations

import logging
from typing import Optional

from litestar import Controller, get
from litestar.exceptions import NotFoundException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.system import SupportChatHistory
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.support_inbox import (
    SupportSessionSummary,
    SupportSessionListResponse,
    SupportChatMessageView,
    SupportSessionDetailResponse,
)
from backend.utils.security import GeminiSecurity

logger = logging.getLogger("api-gateway")


class AdminSupportInboxController(Controller):
    """Admin read-only Inbox: view decrypted Helen chat sessions."""
    path = "/api/v1/admin/support/inbox"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/sessions", summary="List all support chat sessions (paginated)")
    async def list_sessions(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> SupportSessionListResponse:
        """
        Returns one row per unique session_id with summary metadata.
        Groups by session, counts messages, shows last intent + timestamp.
        """
        # Subquery: latest created_at per session
        subq = (
            select(
                SupportChatHistory.session_id,
                func.count(SupportChatHistory.id).label("message_count"),
                func.max(SupportChatHistory.created_at).label("last_message_at"),
            )
            .where(SupportChatHistory.deleted_at.is_(None))
            .group_by(SupportChatHistory.session_id)
            .subquery()
        )

        # Latest record per session for metadata (customer info, intent)
        inner = (
            select(SupportChatHistory)
            .where(SupportChatHistory.deleted_at.is_(None))
            .order_by(
                SupportChatHistory.session_id,
                desc(SupportChatHistory.created_at),
            )
            .distinct(SupportChatHistory.session_id)
        )
        if search:
            inner = inner.where(
                SupportChatHistory.customer_phone.ilike(f"%{search}%")
                | SupportChatHistory.customer_name.ilike(f"%{search}%")
                | SupportChatHistory.product_slug.ilike(f"%{search}%")
            )

        count_q = select(func.count()).select_from(inner.subquery())
        total: int = (await db_session.execute(count_q)).scalar_one_or_none() or 0

        paged = inner.limit(limit).offset(offset)
        rows = (await db_session.execute(paged)).scalars().all()

        # Fetch message counts from subquery results
        count_rows = (await db_session.execute(select(subq))).all()
        count_map: dict[str, int] = {r.session_id: r.message_count for r in count_rows}
        time_map: dict[str, str] = {
            r.session_id: str(r.last_message_at) for r in count_rows
        }

        summaries: list[SupportSessionSummary] = [
            SupportSessionSummary(
                session_id=row.session_id,
                customer_name=row.customer_name or "Khách ẩn danh",
                customer_phone=row.customer_phone,
                product_slug=row.product_slug,
                message_count=count_map.get(row.session_id, 0),
                last_intent=row.intent,
                last_message_at=time_map.get(row.session_id),
            )
            for row in rows
        ]

        return SupportSessionListResponse(data=summaries, total=total)

    @get("/sessions/{session_id:str}", summary="Get decrypted full chat thread for a session")
    async def get_session(
        self,
        db_session: AsyncSession,
        session_id: str,
    ) -> SupportSessionDetailResponse:
        """
        Returns all messages for a session, decrypted.
        Sorted chronologically (oldest first) for inbox-style rendering.
        """
        stmt = (
            select(SupportChatHistory)
            .where(
                SupportChatHistory.session_id == session_id,
                SupportChatHistory.deleted_at.is_(None),
            )
            .order_by(SupportChatHistory.created_at)
        )
        rows = (await db_session.execute(stmt)).scalars().all()
        if not rows:
            raise NotFoundException(detail=f"Session '{session_id}' not found.")

        first = rows[0]
        messages: list[SupportChatMessageView] = []
        for r in rows:
            try:
                decrypted: str = GeminiSecurity.decrypt(r.content) if r.content else ""
            except Exception:
                decrypted = "[Không thể giải mã nội dung]"
            messages.append(
                SupportChatMessageView(
                    id=str(r.id),
                    role=r.role,
                    content=decrypted,
                    intent=r.intent,
                    created_at=str(r.created_at) if r.created_at else None,
                )
            )

        return SupportSessionDetailResponse(
            session_id=session_id,
            customer_name=first.customer_name or "Khách ẩn danh",
            customer_phone=first.customer_phone,
            product_slug=first.product_slug,
            messages=messages,
        )
