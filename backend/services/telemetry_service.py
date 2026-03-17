import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
        duration_ms: int = 0,
        tenant_id: str = "default"
    ) -> None:
        """Log agent telemetry in background via Scalar Insert (Zero-Hydration)."""
        try:
            from sqlalchemy import text
            await session.execute(
                text("""
                    INSERT INTO agent_telemetry_logs (
                        id, session_id, agent_name, intent_hash,
                        input_tokens, output_tokens, cost_token, duration_ms,
                        created_at, updated_at, tenant_id
                    )
                    VALUES (:id, :sid, :name, :hash, :in, :out, :cost, :dur, NOW(), NOW(), :tid)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "sid": session_id,
                    "name": agent_name,
                    "hash": intent_hash,
                    "in": input_tokens,
                    "out": output_tokens,
                    "cost": cost_token,
                    "dur": duration_ms,
                    "tid": tenant_id
                }
            )
            await session.commit()
        except Exception as e:
            logger.error(f"[TelemetryService] Failed to log telemetry: {e}")

telemetry_service = TelemetryService()
