# backend/routers/intent_utils.py
import json
import logging
import asyncio
import uuid
from typing import Dict, Optional
from uuid import UUID

from backend.database.repositories import ChatMessageRepository, AgentTelemetryLogRepository
from backend.database.models import ChatMessage, AgentTelemetryLog
from backend.database.alchemy_config import alchemy_config
from backend.utils.data_stripper import DataStripper

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

# Global background task tracker for memory safety (V76)
background_tasks = set()

def sse(phase: str, data: Dict[str, object]) -> bytes:
    """Format a Server-Sent Event line."""
    return f"data: {json.dumps({'phase': phase, **data}, ensure_ascii=False)}\n\n".encode("utf-8")

async def background_save_logs(
    session_id: str,
    user_id: Optional[UUID] = None,
    data_query: str = "",
    modality: str = "text",
    result_message: str = "",
    result_ui_action: str = "",
    tier_str: str = "",
    data_extra: Optional[Dict[str, object]] = None,
    telemetry_data: Optional[Dict[str, object]] = None,
    is_noise: bool = False
) -> None:
    try:
        async with async_session_maker() as session:
            telemetry_repo = AgentTelemetryLogRepository(session=session)
            chat_repo = ChatMessageRepository(session=session)

            if telemetry_data:
                await telemetry_repo.add(AgentTelemetryLog(**telemetry_data))

            if not is_noise:
                await save_message(chat_repo, session_id, "user", data_query, None, modality, user_id=user_id)
                await save_message(chat_repo, session_id, "assistant", result_message, result_ui_action, modality, tier_str, user_id=user_id, data_extra=data_extra)

            await session.commit()
    except Exception as e:
        logger.error(f"[SSE Background Log Error] {e}")

async def save_message(chat_repo: ChatMessageRepository, session_id: str, role: str, content: str, ui_action: Optional[str], modality: str, router_tier: Optional[str] = None, user_id: Optional[UUID] = None, data_extra: Optional[Dict[str, object]] = None) -> None:
    payload = {"text": content}
    if ui_action:   payload["ui_action"] = ui_action
    if router_tier: payload["router_tier"] = router_tier
    if data_extra:
        if data_extra.get("category") == "CONTENT_CREATE":
            for key in ("category", "campaign_id", "step", "status", "action"):
                if data_extra.get(key) is not None:
                    payload[key] = data_extra[key]
        else:
            payload.update(data_extra)

    await chat_repo.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=payload,
        modality=modality or "text",
    ))
