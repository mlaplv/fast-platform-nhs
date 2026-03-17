import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Union, Tuple, cast
from sqlalchemy import select, delete as sqlalchemy_delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ChatMessage, User
from backend.services.xohi_memory import xohi_memory
from backend.schemas.chat import ChatHistoryResponse, ChatMessageSchema
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center

logger = logging.getLogger("api-gateway")

class ChatService:
    """
    ULTRA-LEAN CHAT SERVICE (ELITE V2.2)
    ------------------------------------
    Handles Chat Persistence, Redis Caching, and Selective Logging.
    """

    async def save_message(
        self,
        session: AsyncSession,
        session_id: str,
        role: str,
        content: Union[str, Dict],
        user_id: Optional[str] = None,
        modality: str = "text",
        data_extra: Optional[Dict] = None
    ) -> str:
        """
        Save a chat message with Selective Persistence and Redis Caching.
        """
        msg_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        # 1. Prepare Content Payload
        if isinstance(content, str):
            payload = {"text": content}
        else:
            payload = content

        if data_extra:
            payload.update(data_extra)

        # 2. Load Settings for Selective Persistence
        profile = await xohi_memory.get_voice_profile(user_id) if user_id else None
        chat_settings = profile.get("chat_settings", {}) if profile else {}

        # 3. Redis Cache (Last 10)
        msg_dict = {
            "id": msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": payload,
            "modality": modality or "text",
            "created_at": created_at.isoformat()
        }
        if user_id:
            cache_limit = chat_settings.get("cache_limit", 10)
            await xohi_memory.add_chat_to_cache(user_id, msg_dict, limit=cache_limit)

        # 4. Selective Persistence Policy
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
                    content=payload,
                    modality=modality or "text",
                    created_at=created_at
                )
                session.add(msg)
                # Note: We rely on caller for commit in multi-op flows, but here it's usually standalone
                return msg_id
            except Exception as e:
                logger.error(f"[ChatService] Failed to persist message: {e}")

        return msg_id

    async def get_chat_history(
        self,
        session: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None,
        user_roles: List[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        user_id_query: Optional[str] = None,
        since_id: Optional[str] = None
    ) -> ChatHistoryResponse:
        """
        Retrieves messages for a session or user using Hybrid Redis/DB strategy.
        Enforces ownership and God-Mode logic.
        """
        user_roles = user_roles or []
        is_super_admin = "SUPER_ADMIN" in user_roles
        target_user_id = user_id

        # ═══ GOD-MODE: ADMIN OVERRIDE ═══
        if is_super_admin and user_id_query:
            target_user_id = user_id_query
            from backend.services.event_bus import event_bus
            await event_bus.emit("SECURITY_AUDIT", {
                "user_id": user_id,
                "type": "SECURITY",
                "message": f"GOD-MODE ACCESS: System logs for user_id '{user_id_query}' accessed"
            })

        # ═══ CACHE BYPASS / REDIS CHECK ═══
        if session_id == "account" and not cursor and limit <= 10 and target_user_id:
            cached = await xohi_memory.get_recent_chat(target_user_id)
            if cached:
                return ChatHistoryResponse(
                    session_id=session_id,
                    has_more=True,
                    next_cursor=str(cached[-1]["id"]),
                    messages=[ChatMessageSchema(**m) for m in reversed(cached)]
                )

        # ═══ OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin and session_id != "account" and target_user_id:
            stmt = select(ChatMessage.user_id).where(ChatMessage.session_id == session_id).limit(1)
            res = await session.execute(stmt)
            owner_id = res.scalar()
            if owner_id and str(owner_id) != target_user_id:
                from litestar.exceptions import HTTPException
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch.")

        # ═══ DB QUERY: SCALAR PROJECTION (Zero-Hydration) ═══
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

        # Cursor Pagination
        if cursor:
            cursor_stmt = select(ChatMessage.created_at).where(ChatMessage.id == cursor)
            cursor_res = await session.execute(cursor_stmt)
            cursor_time = cursor_res.scalar()
            if cursor_time:
                stmt = stmt.where(ChatMessage.created_at < cursor_time)

        # Delta Polling
        if since_id:
            since_stmt = select(ChatMessage.created_at).where(ChatMessage.id == since_id)
            since_res = await session.execute(since_stmt)
            since_time = since_res.scalar()
            if since_time:
                stmt = stmt.where(ChatMessage.created_at > since_time)
                stmt = stmt.order_by(ChatMessage.created_at.asc())
            else:
                stmt = stmt.order_by(ChatMessage.created_at.desc())
        else:
            stmt = stmt.order_by(ChatMessage.created_at.desc())

        res = await session.execute(stmt)
        rows = res.all()

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        messages = []
        for r in rows:
            messages.append(ChatMessageSchema(
                id=str(r.id),
                session_id=r.session_id,
                user_id=str(r.user_id) if r.user_id else None,
                role=r.role,
                content=r.content,
                modality=r.modality,
                created_at=r.created_at,
                updated_at=r.created_at
            ))

        next_cursor = str(messages[-1].id) if messages and not since_id else None
        if not since_id:
            messages.reverse()

        return ChatHistoryResponse(
            session_id=session_id,
            has_more=has_more,
            next_cursor=next_cursor,
            messages=messages
        )

    async def delete_chat_history(
        self,
        session: AsyncSession,
        session_id: str,
        user_email: str,
        user_roles: List[str]
    ) -> Dict[str, str]:
        """Hard deletes all messages for a session or account with audit trail."""
        if "SUPER_ADMIN" not in user_roles:
            from litestar.exceptions import HTTPException
            raise HTTPException(status_code=403, detail="[SECURITY] Unauthorized: Only SUPER_ADMIN can purge system logs.")

        from backend.services.user_service import user_service
        user = await user_service.get_user_by_email(session, user_email)
        user_id = str(user.id) if user else "system"

        # Signal Dispatch (Audit Trail)
        await signal_center.dispatch(
            user_id=user_id,
            signal=SignalSchema(
                message=f"SUCCESS: Chat history cleaned for session '{session_id}' by {user_email}",
                severity=SignalSeverity.INFO,
                signal_type="SECURITY"
            ),
            db_session=session
        )

        if session_id == "account" and user_id != "system":
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.user_id == user_id)
        else:
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.session_id == session_id)

        await session.execute(stmt)
        return {"status": "success", "message": f"All logs for {session_id} have been purged."}

    async def get_recent_messages(
        self,
        session: AsyncSession,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, object]]:
        """
        Fetch recent messages for context using Scalar Projection (Zero-Hydration).
        """
        stmt = (
            select(
                ChatMessage.role,
                ChatMessage.content
            )
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.deleted_at == None
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        return [{"role": row.role, "content": row.content.get("text") if isinstance(row.content, dict) else row.content}
                for row in reversed(result.all())]

chat_service = ChatService()

chat_service = ChatService()
