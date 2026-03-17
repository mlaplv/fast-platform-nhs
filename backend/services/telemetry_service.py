import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import AgentTelemetryLog

logger = logging.getLogger("api-gateway")

class TelemetryService:
    """
    ULTRA-LEAN TELEMETRY SERVICE (ELITE V2.2)
    -----------------------------------------
    Handles Agent Performance Logging and Cost Tracking.
    """

    async def log_telemetry(
        self,
        session: AsyncSession,
        session_id: str,
        agent_name: str,
        intent_hash: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_token: float = 0.0,
        duration_ms: int = 0
    ) -> None:
        """Log agent telemetry in background."""
        try:
            log = AgentTelemetryLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                intent_hash=intent_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_token=cost_token,
                duration_ms=duration_ms
            )
            session.add(log)
            await session.commit()
        except Exception as e:
            logger.error(f"[TelemetryService] Failed to log telemetry: {e}")

telemetry_service = TelemetryService()
