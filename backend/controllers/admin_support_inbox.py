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

from litestar import Controller, get, post
from litestar.exceptions import NotFoundException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.database.models.system import SupportChatHistory
from backend.services.xohi_memory import xohi_memory
from backend.services.event_bus import event_bus
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.support_inbox import (
    SupportSessionSummary,
    SupportSessionListResponse,
    SupportChatMessageView,
    SupportSessionDetailResponse,
    SupportManualMessageRequest,
)
from backend.schemas.support import SupportIntent
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

        summaries: list[SupportSessionSummary] = []
        for row in rows:
            sid = row.session_id
            is_takeover = await xohi_memory.client.get(f"support:takeover:{sid}") == "1"
            summaries.append(
                SupportSessionSummary(
                    session_id=sid,
                    customer_name=row.customer_name or "Khách ẩn danh",
                    customer_phone=row.customer_phone,
                    product_slug=row.product_slug,
                    message_count=count_map.get(sid, 0),
                    last_intent=row.intent,
                    last_message_at=time_map.get(sid),
                    is_takeover=is_takeover
                )
            )

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

        is_takeover = await xohi_memory.client.get(f"support:takeover:{session_id}") == "1"

        return SupportSessionDetailResponse(
            session_id=session_id,
            customer_name=first.customer_name or "Khách ẩn danh",
            customer_phone=first.customer_phone,
            product_slug=first.product_slug,
            messages=messages,
            is_takeover=is_takeover
        )

    @post("/sessions/{session_id:str}/takeover", summary="Toggle AI Takeover for a session")
    async def toggle_takeover(self, session_id: str) -> dict[str, bool]:
        """Enable or disable AI for a specific session via Redis."""
        key = f"support:takeover:{session_id}"
        current = await xohi_memory.client.get(key)
        new_state = "1" if current != "1" else "0"
        await xohi_memory.client.set(key, new_state, ex=86400 * 3) # 3 days TTL
        
        return {"is_takeover": new_state == "1"}

    @post("/sessions/{session_id:str}/message", summary="Send a manual message as high-level representative")
    async def send_manual_message(
        self,
        db_session: AsyncSession,
        session_id: str,
        data: SupportManualMessageRequest,
    ) -> SupportChatMessageView:
        """
        Manually send a message to the customer.
        Saves to history as 'assistant' but with 'MANUAL' intent.
        Emits Pulse signal to trigger real-time UI updates on client & admin side.
        """
        # Fetch session metadata to maintain customer context
        meta_stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).limit(1)
        meta_res = await db_session.execute(meta_stmt)
        meta = meta_res.scalar_one_or_none()
        
        if not meta:
            raise NotFoundException(detail="Session not found.")

        # Encrypt and save
        msg_id = f"manual_{datetime.now().timestamp()}"
        enc_content = GeminiSecurity.encrypt(data.message)
        
        new_msg = SupportChatHistory(
            session_id=session_id,
            role="assistant",
            content=enc_content,
            intent="MANUAL",
            customer_name=meta.customer_name,
            customer_phone=meta.customer_phone,
            product_slug=meta.product_slug
        )
        db_session.add(new_msg)
        await db_session.commit()
        await db_session.refresh(new_msg)

        # 🚀 Pulse Broadcaster: Zero-Latency Sync + "Ting" Sound
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "message": data.message,
            "role": "assistant"
        })

        return SupportChatMessageView(
            id=str(new_msg.id),
            role="assistant",
            content=data.message,
            intent="MANUAL",
            created_at=str(new_msg.created_at)
        )
