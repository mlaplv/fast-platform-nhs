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
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER

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
        filter: str = "all",
    ) -> SupportSessionListResponse:
        """
        Returns one row per unique session_id with summary metadata.
        Groups by session, counts messages, shows last intent + timestamp.
        """
        # Fetch unread session IDs from Redis Set (O(1) Memory & Latency compliant thưa sếp)
        unread_sids: set[str] = set()
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                unread_sids = set(await xohi_memory.client.smembers("support:unread_sessions"))
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to get unread sessions from Redis: {e}")

        is_trash_filter = filter == "trash"
        
        # Subquery: message count, latest time, and any-phone detected per session
        subq = (
            select(
                SupportChatHistory.session_id,
                func.count(SupportChatHistory.id).label("message_count"),
                func.max(SupportChatHistory.created_at).label("last_message_at"),
                func.max(SupportChatHistory.customer_phone).label("any_phone"),
            )
            .where(
                SupportChatHistory.deleted_at.isnot(None) if is_trash_filter 
                else SupportChatHistory.deleted_at.is_(None)
            )
            .group_by(SupportChatHistory.session_id)
            .subquery()
        )

        # Core Query: Join SupportChatHistory with subq on session_id and created_at = last_message_at
        # This gives us EXACTLY one record per session (the latest one) sorted by last_message_at DESC!
        stmt = (
            select(SupportChatHistory)
            .join(
                subq,
                (SupportChatHistory.session_id == subq.c.session_id)
                & (SupportChatHistory.created_at == subq.c.last_message_at)
            )
            .order_by(desc(subq.c.last_message_at))
        )

        if search:
            stmt = stmt.where(
                SupportChatHistory.customer_phone.ilike(f"%{search}%")
                | SupportChatHistory.customer_name.ilike(f"%{search}%")
                | SupportChatHistory.product_slug.ilike(f"%{search}%")
            )

        if filter == "unread":
            if unread_sids:
                stmt = stmt.where(SupportChatHistory.session_id.in_(list(unread_sids)))
            else:
                stmt = stmt.where(SupportChatHistory.session_id == "EMPTY_FILTER_NO_UNREAD")
        elif filter == "read":
            if unread_sids:
                stmt = stmt.where(~SupportChatHistory.session_id.in_(list(unread_sids)))

        count_q = select(func.count()).select_from(stmt.subquery())
        total: int = (await db_session.execute(count_q)).scalar_one_or_none() or 0

        paged = stmt.limit(limit).offset(offset)
        rows = (await db_session.execute(paged)).scalars().all()

        # Fetch aggregated results from subquery
        agg_res = (await db_session.execute(select(subq))).all()
        count_map: dict[str, int] = {r.session_id: r.message_count for r in agg_res}
        time_map: dict[str, str] = {r.session_id: str(r.last_message_at) for r in agg_res}
        phone_map: dict[str, str | None] = {r.session_id: r.any_phone for r in agg_res}

        high_intent_codes = ["PURCHASE", "CLOSING", "PAYMENT", "ORDER_CONFIRM", "CHECKOUT", "DEPOSIT"]

        summaries: list[SupportSessionSummary] = []
        for row in rows:
            sid = row.session_id
            is_takeover = await xohi_memory.client.get(f"support:takeover:{sid}") == "0"
            is_online = await xohi_memory.client.get(f"support:presence:{sid}") == "1"
            intent_str = (row.intent or "").upper()
            has_phone = bool(phone_map.get(sid))
            
            # Elite V2.2 Emergency: Any Phone detected in session history forces High Intent status
            is_high = has_phone or intent_str in high_intent_codes
            is_unread = sid in unread_sids
            is_trash = row.deleted_at is not None
            
            summaries.append(
                SupportSessionSummary(
                    session_id=sid,
                    customer_name=row.customer_name or "Khách ẩn danh",
                    customer_phone=phone_map.get(sid) or row.customer_phone,
                    product_slug=row.product_slug,
                    message_count=count_map.get(sid, 0),
                    last_intent=row.intent,
                    last_message_at=time_map.get(sid),
                    is_takeover=is_takeover,
                    is_high_intent=is_high,
                    is_online=is_online,
                    is_unread=is_unread,
                    is_trash=is_trash
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
        # First, try to query active messages
        stmt = (
            select(SupportChatHistory)
            .where(
                SupportChatHistory.session_id == session_id,
                SupportChatHistory.deleted_at.is_(None),
            )
            .order_by(SupportChatHistory.created_at)
        )
        rows = (await db_session.execute(stmt)).scalars().all()
        
        # If no active messages, check if it exists in trash (soft-deleted)
        if not rows:
            stmt_trash = (
                select(SupportChatHistory)
                .where(
                    SupportChatHistory.session_id == session_id,
                    SupportChatHistory.deleted_at.isnot(None),
                )
                .order_by(SupportChatHistory.created_at)
            )
            rows = (await db_session.execute(stmt_trash)).scalars().all()

        if not rows:
            raise NotFoundException(detail=f"Session '{session_id}' not found.")

        first = rows[0]
        messages: list[SupportChatMessageView] = []
        for r in rows:
            try:
                decrypted: str = GeminiSecurity.decrypt(r.content) if r.content else ""
                
                # Elite V2.2: Ensure internal trigger is hidden from the Admin inbox as well
                if decrypted == HELEN_FOLLOW_UP_TRIGGER:
                    continue
                    
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Decryption failed for message {r.id}: {e}")
                decrypted = "[Không thể giải mã nội dung]"
                
            messages.append(
                SupportChatMessageView(
                    id=str(r.id),
                    role=r.role,
                    content=decrypted,
                    intent=r.intent,
                    created_at=str(r.created_at) if r.created_at else None,
                    is_revoked=r.is_revoked
                )
            )

        is_takeover = await xohi_memory.client.get(f"support:takeover:{session_id}") == "0"
        is_online = await xohi_memory.client.get(f"support:presence:{session_id}") == "1"

        # Mark as read in Redis (O(1) Set compliance thưa sếp)
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.srem("support:unread_sessions", session_id)
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to clear unread in Redis: {e}")

        return SupportSessionDetailResponse(
            session_id=session_id,
            customer_name=first.customer_name or "Khách ẩn danh",
            customer_phone=first.customer_phone,
            product_slug=first.product_slug,
            messages=messages,
            is_takeover=is_takeover,
            is_online=is_online
        )

    @post("/sessions/{session_id:str}/read", summary="Toggle read/unread status for a session")
    async def mark_session_read(
        self,
        session_id: str,
        is_unread: bool,
    ) -> dict[str, bool]:
        """Manually mark a session as unread or read using Redis Set (O(1) compliance thưa sếp)"""
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                if is_unread:
                    await xohi_memory.client.sadd("support:unread_sessions", session_id)
                else:
                    await xohi_memory.client.srem("support:unread_sessions", session_id)
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to toggle unread in Redis: {e}")
        
        # Emit event to sync with other admins
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "is_unread": is_unread
        })
        return {"is_unread": is_unread}

    @post("/sessions/{session_id:str}/trash", summary="Move session to trash (soft delete)")
    async def move_to_trash(
        self,
        db_session: AsyncSession,
        session_id: str,
    ) -> dict[str, bool]:
        """Soft delete all messages in a session by setting deleted_at = utcnow()"""
        stmt = select(SupportChatHistory).where(
            SupportChatHistory.session_id == session_id,
            SupportChatHistory.deleted_at.is_(None)
        )
        messages = (await db_session.execute(stmt)).scalars().all()
        
        from backend.database.models.base import utcnow
        now = utcnow()
        
        for msg in messages:
            msg.deleted_at = now
        await db_session.commit()
        
        # Also clean up unread status from Redis
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.srem("support:unread_sessions", session_id)
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to clear unread in Redis: {e}")

        # Emit update event
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "action": "trash"
        })
        return {"ok": True}

    @post("/sessions/{session_id:str}/restore", summary="Restore session from trash")
    async def restore_from_trash(
        self,
        db_session: AsyncSession,
        session_id: str,
    ) -> dict[str, bool]:
        """Restore soft-deleted session messages by setting deleted_at = None"""
        stmt = select(SupportChatHistory).where(
            SupportChatHistory.session_id == session_id,
            SupportChatHistory.deleted_at.isnot(None)
        )
        messages = (await db_session.execute(stmt)).scalars().all()
        for msg in messages:
            msg.deleted_at = None
        await db_session.commit()
        
        # Emit update event
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "action": "restore"
        })
        return {"ok": True}

    @post("/sessions/{session_id:str}/hard-delete", summary="Permanently delete a session")
    async def hard_delete_session(
        self,
        db_session: AsyncSession,
        session_id: str,
    ) -> dict[str, bool]:
        """Permanently delete all messages in a session from database"""
        from sqlalchemy import delete
        stmt = delete(SupportChatHistory).where(SupportChatHistory.session_id == session_id)
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Also clean up unread from Redis
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.srem("support:unread_sessions", session_id)
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to clear unread in Redis: {e}")
                
        # Emit update event
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "action": "hard-delete"
        })
        return {"ok": True}

    @post("/sessions/{session_id:str}/takeover", summary="Toggle AI Takeover for a session")
    async def toggle_takeover(self, session_id: str) -> dict[str, bool]:
        """Enable or disable AI for a specific session via Redis."""
        key = f"support:takeover:{session_id}"
        current = await xohi_memory.client.get(key)
        new_state = "1" if current == "0" else "0"
        await xohi_memory.client.set(key, new_state, ex=86400 * 3) # 3 days TTL
        
        return {"is_takeover": new_state == "0"}

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

        # Mark as read in Redis since admin replied (O(1) Set compliance thưa sếp)
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.srem("support:unread_sessions", session_id)
            except Exception as e:
                logger.error(f"[AdminSupportInbox] Failed to clear unread in Redis: {e}")

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
    
    @post("/sessions/{session_id:str}/messages/{message_id:str}/revoke", summary="Revoke (or un-revoke) a message")
    async def revoke_message(
        self,
        db_session: AsyncSession,
        session_id: str,
        message_id: str
    ) -> dict[str, bool]:
        """ Toggles the is_revoked flag for a message and notifies browsers via Pulse. """
        stmt = select(SupportChatHistory).where(
            SupportChatHistory.session_id == session_id,
            SupportChatHistory.id == message_id
        )
        msg = (await db_session.execute(stmt)).scalar_one_or_none()
        
        if not msg:
            raise NotFoundException(detail="Tin nhắn không tồn tại.")
        
        msg.is_revoked = not msg.is_revoked
        await db_session.commit()

        # Emit sync signal for real-time hiding in Active UI (Admin & Client)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "message_id": message_id,
            "is_revoked": msg.is_revoked
        })
        
        return {"is_revoked": msg.is_revoked}
