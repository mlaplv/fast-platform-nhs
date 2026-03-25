import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import HTTPException

from backend.database.models import ChatMessage, User
from backend.database.repositories import UserRepository
from backend.schemas.chat import ChatMessageSchema, ChatHistoryResponse
from backend.schemas.common import SuccessResponse
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center
from backend.services.xohi_memory import xohi_memory
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

class ChatService:
    @staticmethod
    async def persist_message(
        db_session: AsyncSession,
        session_id: str,
        user_id: Optional[str],
        role: str,
        content: str,
        modality: Optional[str] = "text"
    ) -> SuccessResponse:
        """Move logic from ChatController.save_message."""
        if role not in ("user", "assistant"):
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'assistant'.")

        msg_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        # ═══ R30/R74: LOAD SETTINGS FIRST ═══
        profile = await xohi_memory.get_voice_profile(user_id) if user_id else None
        chat_settings = profile.get("chat_settings", {}) if profile else {}

        # ═══ REDIS CACHE: Redis-Last-10 ═══
        msg_dict = {
            "id": msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "modality": modality or "text",
            "created_at": created_at.isoformat()
        }
        if user_id:
            cache_limit = chat_settings.get("cache_limit", 10)
            await xohi_memory.add_chat_to_cache(user_id, msg_dict, limit=cache_limit)

        # ═══ R30/R74: SELECTIVE PERSISTENCE ═══
        is_user = role == "user"
        is_voice = modality == "voice"
        is_assistant = role == "assistant"

        selective = chat_settings.get("selective_persistence", True)
        save_ai = chat_settings.get("save_ai_responses", False)

        should_persist = False
        if selective:
            if is_user or is_voice:
                should_persist = True
        else:
            should_persist = True
            if is_assistant and not save_ai:
                should_persist = False

        if should_persist:
            try:
                msg = ChatMessage(
                    id=msg_id,
                    session_id=session_id,
                    user_id=user_id,
                    role=role,
                    content=content,
                    modality=modality or "text",
                    created_at=created_at
                )
                db_session.add(msg)
                return SuccessResponse(ok=True, id=msg_id, data={"persisted": True})
            except Exception as e:
                logger.error(f"[ChatMessage] POST save failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to persist critical message.")

        return SuccessResponse(ok=True, id=msg_id, data={"persisted": False})

    @staticmethod
    async def get_history(
        db_session: AsyncSession,
        session_id: str,
        user_id: Optional[str],
        roles: List[str],
        cursor: Optional[str] = None,
        limit: int = 20,
        user_id_query: Optional[str] = None,
        since_id: Optional[str] = None
    ) -> ChatHistoryResponse:
        """Moves logic from ChatController.get_chat_history. Implements Scalar Projection (Rule 1.5)."""
        is_super_admin: bool = "SUPER_ADMIN" in roles
        target_user_id: Optional[str] = user_id

        # ═══ GOD-MODE: ADMIN OVERRIDE ═══
        if is_super_admin and user_id_query:
            target_user_id = user_id_query
            await event_bus.emit("SECURITY_AUDIT", {
                "user_id": user_id,
                "type": "SECURITY",
                "message": f"GOD-MODE ACCESS: System logs for user_id '{user_id_query}' accessed by {user_id}"
            })

        # ═══ CACHE BYPASS / REDIS CHECK ═══
        if session_id == "account" and not cursor and limit <= 10 and target_user_id:
            cached_data: List[Dict[str, Any]] = await xohi_memory.get_recent_chat(target_user_id)
            if cached_data:
                # Elite V2.2: Ensure precise type handling for indexing
                last_msg: Dict[str, Any] = cached_data[-1]
                return ChatHistoryResponse(
                    session_id=session_id,
                    has_more=True,
                    next_cursor=str(last_msg["id"]),
                    messages=[ChatMessageSchema(**m) for m in reversed(cached_data)]
                )

        # ═══ OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin and session_id != "account" and target_user_id:
            stmt = select(ChatMessage.user_id).where(ChatMessage.session_id == session_id).limit(1)
            res = await db_session.execute(stmt)
            owner_id = res.scalar()
            if owner_id and str(owner_id) != target_user_id:
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch.")

        # ═══ DB QUERY: SCALAR PROJECTION (V56.0) ═══
        cols = [
            ChatMessage.id, ChatMessage.session_id, ChatMessage.user_id,
            ChatMessage.role, ChatMessage.content, ChatMessage.modality,
            ChatMessage.created_at
        ]
        stmt = select(*cols).where(ChatMessage.deleted_at == None)

        if session_id == "account" and target_user_id:
            stmt = stmt.where(ChatMessage.user_id == target_user_id)
        else:
            stmt = stmt.where(ChatMessage.session_id == session_id)

        if cursor:
            cursor_stmt = select(ChatMessage.created_at).where(ChatMessage.id == cursor)
            cursor_res = await db_session.execute(cursor_stmt)
            cursor_time = cursor_res.scalar()
            if cursor_time:
                stmt = stmt.where(ChatMessage.created_at < cursor_time)

        if since_id:
            since_stmt = select(ChatMessage.created_at).where(ChatMessage.id == since_id)
            since_res = await db_session.execute(since_stmt)
            since_time = since_res.scalar()
            if since_time:
                stmt = stmt.where(ChatMessage.created_at > since_time)
                stmt = stmt.order_by(ChatMessage.created_at.asc())
            else:
                stmt = stmt.order_by(ChatMessage.created_at.desc())
        else:
            stmt = stmt.order_by(ChatMessage.created_at.desc())

        res = await db_session.execute(stmt)
        rows = res.all()

        has_more: bool = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        messages_list: List[ChatMessageSchema] = [ChatMessageSchema.model_validate(dict(r._mapping)) for r in rows]
        next_cursor: Optional[str] = str(messages_list[-1].id) if messages_list and not since_id else None

        if not since_id:
            messages_list.reverse()

        return ChatHistoryResponse(
            session_id=session_id,
            has_more=has_more,
            next_cursor=next_cursor,
            messages=messages_list
        )

    @staticmethod
    async def clear_history(
        db_session: AsyncSession,
        session_id: str,
        user_id: Optional[str],
        user_email: str,
        roles: List[str],
        user_id_query: Optional[str] = None
    ) -> SuccessResponse:
        """
        [NUCLEAR PURGE] Absolute cleanup (DB + Redis + Logs).
        Rule: "Sạch kin kít" - No audit trails left for this session.
        Uses Repositories to handle tenant-aware hard deletes.
        """
        from backend.database.repositories import ChatMessageRepository, NotificationRepository
        is_super_admin: bool = "SUPER_ADMIN" in roles
        target_user_id: Optional[str] = user_id

        # ═══ GOD-MODE: ADMIN OVERRIDE ═══
        if is_super_admin and user_id_query:
            target_user_id = user_id_query

        # ═══ OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin:
            if session_id == "account" and target_user_id != user_id:
                raise HTTPException(status_code=403, detail="[SECURITY] Unauthorized: Identity mismatch for account purge.")

        # ═══ PHASE 1: DB PURGE (ChatMessage) ═══
        chat_repo = ChatMessageRepository(session=db_session)
        if session_id == "account" and target_user_id:
            # Delete all messages for user across all sessions
            await chat_repo.delete_where(user_id=target_user_id)
            deleted_count = "ALL"
        else:
            await chat_repo.delete_where(session_id=session_id)
            deleted_count = "SESSION"

        # ═══ PHASE 2: DB PURGE (Notifications) ═══
        if target_user_id:
            notif_repo = NotificationRepository(session=db_session)
            await notif_repo.delete_where(user_id=target_user_id)

        # ═══ PHASE 3: REDIS PURGE ═══
        if target_user_id:
            await xohi_memory.delete_pattern(f"xohi:chat:{target_user_id}")
        
        logger.info(f"💣 [NuclearPurge] Swept {deleted_count} messages and all notifications for target={target_user_id}")

        # transient SSE event for the UI toast
        await event_bus.emit(f"chat:purged:{target_user_id or session_id}", {"ok": True})

        return SuccessResponse(ok=True, message=f"All logs for {session_id} have been purged.")

chat_service = ChatService()
