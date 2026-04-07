import logging
import asyncio
import httpx
import uuid
import unicodedata
from base64 import b64encode
from typing import Dict, Optional, List, cast

from litestar import WebSocket
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import AgentTelemetryLogRepository
from backend.database.models import AgentTelemetryLog

from backend.services.routing.stt_service import stt_service

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

# Minimum audio size to avoid sending silence/noise (bytes)
MIN_AUDIO_BYTES = 1500
# Maximum audio buffer size (20MB safe limit)
MAX_AUDIO_BYTES = 20_000_000

async def transcribe(audio_data: bytes, user_id: Optional[str] = None) -> str:
    """精英 V2.2: Thin wrapper for the unified STT Service."""
    if not audio_data or len(audio_data) < MIN_AUDIO_BYTES:
        return ""
    
    # Delegate to the unified service which handles Raw + Correction
    return await stt_service.transcribe(audio_data, user_id)

async def background_save_telemetry(
    session_id: str,
    agent_name: str,
    duration_ms: int,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_token: float = 0.0,
    intent_hash: str = "stt_op"
) -> None:
    """Save performance metrics to database in background."""
    try:
        async with async_session_maker() as session:
            repo = AgentTelemetryLogRepository(session=session)
            await repo.add(AgentTelemetryLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                intent_hash=intent_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_token=cost_token,
                duration_ms=duration_ms
            ))
            await session.commit()
    except Exception as e:
        logger.error(f"[STT Telemetry Error] {e}")
