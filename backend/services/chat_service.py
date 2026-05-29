import uuid
import base64
import logging
from backend.utils.uid import new_id
from datetime import datetime, timezone
from typing import Optional, List, Dict, Union, TypedDict

from sqlalchemy import select, delete as sql_delete
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

# [Elite V2.2] Hard cap: bảo vệ khỏi requests lạm dụng ?limit=99999
CHAT_MAX_LIMIT: int = 50
# Default Redis cache size — match với add_chat_to_cache default
CHAT_CACHE_SIZE: int = 20

logger = logging.getLogger("api-gateway")

class CachedChatMsg(TypedDict):
    id: str
    session_id: str
    user_id: Optional[str]
    role: str
    content: str
    modality: str
    created_at: str

class ChatService:
    # CNS V86.11: Persistence Noise-Gate Patterns
    NOISE_PATTERNS = {
        "mở index", "mở trang quản trị", "mở brain", "mở inbox", "manage skills", 
        "mở chiến dịch", "mở tò mò", "mở tri thức", "mở thống kê"
    }

    @classmethod
    async def persist_message(
        cls,
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

        msg_id = new_id()
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
            cache_limit = chat_settings.get("cache_limit", CHAT_CACHE_SIZE)
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
            # [CNS V86.12] State Resilience: Always persist assistant messages containing UI actions or campaign state
            elif is_assistant and isinstance(content, dict) and (content.get("ui_action") or content.get("campaign_id")):
                should_persist = True
        else:
            should_persist = True
            if is_assistant and not save_ai:
                should_persist = False

        # ═══ CNS V86.11: ROOT NOISE FILTERING (DB Bloat Prevention) ═══
        # Rule: Do not persist navigation triggers or procedural bot confirmations to DB.
        # If content is a dict (JSONB), extract the text part.
        text_content = content.get("text", "") if isinstance(content, dict) else content
        clean_content = str(text_content).lower().strip()
        
        is_noise = False
        if is_user and clean_content in cls.NOISE_PATTERNS:
            is_noise = True
        elif is_assistant and ("em mở" in clean_content or "dạ sếp" in clean_content):
            # Targeted bot confirmations for navigation
            noise_targets = ["trang quản trị", "brain", "index", "inbox", "tri thức", "chiến dịch"]
            if any(x in clean_content for x in noise_targets):
                is_noise = True
            
        if is_noise:
            should_persist = False
            preview = f"'{content[:30]}...'" if isinstance(content, str) else "structured data"
            logger.debug(f"[ChatService] Noise-Gate: Blocked persistence for {preview}")

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
    def _encode_cursor(created_at: datetime, msg_id: str) -> str:
        """
        [Bug #7 Fix] Opaque Base64 cursor — Zalo/Messenger standard.
        Encode timestamp + id thành cursor string, decode không cần extra DB query.
        """
        raw = f"{created_at.isoformat()}|{msg_id}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    @staticmethod
    def _decode_cursor(cursor: str) -> Optional[tuple[datetime, str]]:
        """Decode opaque cursor. Return None nếu cursor cũ (ID format) hoặc invalid."""
        try:
            raw = base64.urlsafe_b64decode(cursor.encode()).decode()
            ts_str, msg_id = raw.split("|", 1)
            return datetime.fromisoformat(ts_str), msg_id
        except Exception:
            # Backwards compat: cursor cũ là UUID thuần — trả None để fallback DB lookup
            return None

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
        """[Bug #1 #4 #7 Fix] Keyset Pagination chuẩn Zalo/Messenger.
        - DB-level LIMIT (không load toàn bộ vào RAM)
        - Opaque Base64 cursor (không cần extra DB query)
        - Cache-hit không phụ thuộc limit (initial load = no cursor)
        """
        # [Bug #1 Hard-cap] Bảo vệ khỏi ?limit=99999
        limit = min(limit, CHAT_MAX_LIMIT)

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

        # ═══ [Bug #4 Fix] CACHE HIT: Initial page load (no cursor, no since_id) ═══
        # Không ràng buộc limit<=10 nữa — cache hit bất cứ khi nào là initial load
        if session_id == "account" and not cursor and not since_id and target_user_id:
            cached_data: List[CachedChatMsg] = await xohi_memory.get_recent_chat(
                target_user_id, limit=limit  # type: ignore
            )
            if cached_data:
                last_msg: CachedChatMsg = cached_data[-1]
                next_cur = ChatService._encode_cursor(
                    datetime.fromisoformat(str(last_msg["created_at"])),
                    str(last_msg["id"])
                )
                return ChatHistoryResponse(
                    session_id=session_id,
                    has_more=True,
                    next_cursor=next_cur,
                    messages=[ChatMessageSchema(**m) for m in reversed(cached_data)]
                )

        # ═══ OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin and session_id != "account" and target_user_id:
            stmt = select(ChatMessage.user_id).where(ChatMessage.session_id == session_id).limit(1)
            res = await db_session.execute(stmt)
            owner_id = res.scalar()
            if owner_id and str(owner_id) != target_user_id:
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch.")

        # ═══ DB QUERY: SCALAR PROJECTION + KEYSET PAGINATION ═══
        cols = [
            ChatMessage.id, ChatMessage.session_id, ChatMessage.user_id,
            ChatMessage.role, ChatMessage.content, ChatMessage.modality,
            ChatMessage.created_at
        ]
        stmt = select(*cols).where(ChatMessage.deleted_at == None)  # noqa: E711

        if session_id == "account" and target_user_id:
            stmt = stmt.where(ChatMessage.user_id == target_user_id)
        else:
            stmt = stmt.where(ChatMessage.session_id == session_id)

        # ═══ [Bug #7 Fix] OPAQUE CURSOR — không cần extra DB round-trip ═══
        if cursor:
            decoded = ChatService._decode_cursor(cursor)
            if decoded:
                # New opaque cursor: decode trực tiếp
                cursor_time, cursor_id = decoded
                stmt = stmt.where(
                    (ChatMessage.created_at < cursor_time) |
                    ((ChatMessage.created_at == cursor_time) & (ChatMessage.id < cursor_id))
                )
            else:
                # Backwards compat: cursor cũ là UUID — 1 lần DB lookup rồi thôi
                cursor_stmt = select(ChatMessage.created_at).where(ChatMessage.id == cursor)
                cursor_res = await db_session.execute(cursor_stmt)
                cursor_time_legacy = cursor_res.scalar()
                if cursor_time_legacy:
                    stmt = stmt.where(ChatMessage.created_at < cursor_time_legacy)

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

        # ═══ [Bug #1 Fix] DB-LEVEL LIMIT — Không load toàn bộ N rows vào RAM ═══
        stmt = stmt.limit(limit + 1)  # +1 để detect has_more mà không cần count(*)

        res = await db_session.execute(stmt)
        rows = res.all()

        has_more: bool = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        messages_list: List[ChatMessageSchema] = [
            ChatMessageSchema.model_validate(dict(r._mapping)) for r in rows
        ]

        # Build opaque cursor từ last message
        next_cursor: Optional[str] = None
        if messages_list and has_more and not since_id:
            last = messages_list[-1]
            next_cursor = ChatService._encode_cursor(last.createdAt, str(last.id))

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
        [Bug #2 Fix] NUCLEAR PURGE — Dùng sqlalchemy.delete() thay vì delete_where() không tồn tại.
        Rule: "Sạch kin kít" - No audit trails left for this session.
        """
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
        if session_id == "account" and target_user_id:
            stmt_chat = sql_delete(ChatMessage).where(ChatMessage.user_id == target_user_id)
            deleted_count = "ALL"
        else:
            stmt_chat = sql_delete(ChatMessage).where(ChatMessage.session_id == session_id)
            deleted_count = "SESSION"
        await db_session.execute(stmt_chat)

        # ═══ PHASE 2: DB PURGE (Notifications) ═══
        from backend.database.models import Notification
        if target_user_id:
            stmt_notif = sql_delete(Notification).where(Notification.user_id == target_user_id)
            await db_session.execute(stmt_notif)

        # ═══ PHASE 3: REDIS PURGE ═══
        if target_user_id:
            await xohi_memory.delete_pattern(f"xohi:chat:{target_user_id}")

        logger.info(f"💣 [NuclearPurge] Swept {deleted_count} messages and all notifications for target={target_user_id}")

        # transient SSE event for the UI toast
        await event_bus.emit(f"chat:purged:{target_user_id or session_id}", {"ok": True})

        return SuccessResponse(ok=True, message=f"All logs for {session_id} have been purged.")

chat_service = ChatService()
