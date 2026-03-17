import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import ChatMessage
from backend.services.xohi_memory import xohi_memory

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
        Matches the logic in ChatController but moved to Service.
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
        # User/Voice = Persistent. AI = Ephemeral (unless configured otherwise).
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
                await session.commit()
                return msg_id
            except Exception as e:
                logger.error(f"[ChatService] Failed to persist message: {e}")
                # Don't raise here, we want the system to keep working even if logging fails

        return msg_id

    async def get_recent_messages(
        self,
        session: AsyncSession,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, object]]:
        """
        Fetch recent messages for context using Scalar Projection (Zero-Hydration).
        """
        from sqlalchemy import select
        from backend.database.models import ChatMessage

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
        # Reverse to get chronological order for AI context
        return [{"role": row.role, "content": row.content.get("text") if isinstance(row.content, dict) else row.content}
                for row in reversed(result.all())]

chat_service = ChatService()
