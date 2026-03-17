# backend/api/v1/controllers/voice/telemetry.py
import logging
import uuid
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import AgentTelemetryLogRepository
from backend.database.models.system import AgentTelemetryLog

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

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
