import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Union, Tuple, cast
from sqlalchemy import select, delete as sqlalchemy_delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

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
                # Rule R1.5: Zero-Hydration Scalar Insert
                await session.execute(
                    text("""
                        INSERT INTO chat_messages (id, session_id, user_id, role, content, modality, created_at, updated_at, tenant_id)
                        VALUES (:id, :sid, :uid, :role, :content, :mod, :now, :now, :tid)
                    """),
                    {
                        "id": msg_id,
                        "sid": session_id,
                        "uid": user_id,
                        "role": role,
                        "content": payload,
                        "mod": modality or "text",
                        "now": created_at,
                        "tid": profile.get("tenant_id", "default") if profile else "default"
                    }
                )
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
        Enforces ownership and God-Mode logic via Raw SQL (Rule 1.5).
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

        # ═══ OWNERSHIP ENFORCEMENT (Zero-Hydration) ═══
        if not is_super_admin and session_id != "account" and target_user_id:
            owner_sql = text("SELECT user_id FROM chat_messages WHERE session_id = :sid LIMIT 1")
            res_owner = await session.execute(owner_sql, {"sid": session_id})
            owner_id = res_owner.scalar()
            if owner_id and str(owner_id) != target_user_id:
                from litestar.exceptions import HTTPException
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch.")

        # ═══ DB QUERY: SCALAR PROJECTION (Zero-Hydration) ═══
        conditions = ["deleted_at IS NULL"]
        params = {"limit": limit + 1} # Fetch one extra to determine has_more

        if session_id == "account" and target_user_id:
            conditions.append("user_id = :uid")
            params["uid"] = target_user_id
        else:
            conditions.append("session_id = :sid")
            params["sid"] = session_id

        # Cursor Pagination (Zero-Hydration)
        if cursor:
            time_sql = text("SELECT created_at FROM chat_messages WHERE id = :cid")
            time_res = await session.execute(time_sql, {"cid": cursor})
            cursor_time = time_res.scalar()
            if cursor_time:
                conditions.append("created_at < :ctime")
                params["ctime"] = cursor_time

        # Delta Polling
        if since_id:
            since_time_sql = text("SELECT created_at FROM chat_messages WHERE id = :sid_id")
            since_res = await session.execute(since_time_sql, {"sid_id": since_id})
            since_time = since_res.scalar()
            if since_time:
                conditions.append("created_at > :stime")
                params["stime"] = since_time
                order_by = "created_at ASC"
            else:
                order_by = "created_at DESC"
        else:
            order_by = "created_at DESC"

        sql = text(f"""
            SELECT id, session_id, user_id, role, content, modality, created_at
            FROM chat_messages
            WHERE {" AND ".join(conditions)}
            ORDER BY {order_by}
            LIMIT :limit
        """)

        res = await session.execute(sql, params)
        rows = res.all()

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        messages = [
            ChatMessageSchema(
                id=str(r[0]),
                session_id=r[1],
                user_id=str(r[2]) if r[2] else None,
                role=r[3],
                content=r[4],
                modality=r[5],
                created_at=r[6],
                updated_at=r[6]
            )
            for r in rows
        ]

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
        """Hard deletes all messages for a session or account with audit trail via Raw SQL."""
        if "SUPER_ADMIN" not in user_roles:
            from litestar.exceptions import HTTPException
            raise HTTPException(status_code=403, detail="[SECURITY] Unauthorized: Only SUPER_ADMIN can purge system logs.")

        # Zero-Hydration lookup
        user_sql = text("SELECT id FROM users WHERE email = :email LIMIT 1")
        res_user = await session.execute(user_sql, {"email": user_email})
        user_id = str(res_user.scalar()) if res_user.first() else "system"

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
            purge_sql = text("DELETE FROM chat_messages WHERE user_id = :uid")
            await session.execute(purge_sql, {"uid": user_id})
        else:
            purge_sql = text("DELETE FROM chat_messages WHERE session_id = :sid")
            await session.execute(purge_sql, {"sid": session_id})

        await session.commit()
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
        sql = text("""
            SELECT role, content
            FROM chat_messages
            WHERE session_id = :sid AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await session.execute(sql, {"sid": session_id, "limit": limit})
        rows = result.all()
        return [
            {"role": r[0], "content": r[1].get("text") if isinstance(r[1], dict) else r[1]}
            for r in reversed(rows)
        ]

chat_service = ChatService()
