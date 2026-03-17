import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")

class HealthService:
    """
    ULTRA-LEAN HEALTH SERVICE (ELITE V2.2)
    --------------------------------------
    Handles system health checks and anomaly detection.
    """

    async def get_system_anomalies(self, session: AsyncSession) -> List[Dict[str, object]]:
        """Fetch recent anomalies from notifications table."""
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Scalar query to fetch recent alerts
        stmt = text("""
            SELECT id, type, message, created_at
            FROM notifications
            WHERE type IN ('WARNING', 'CRITICAL')
            AND created_at > :since
            ORDER BY created_at DESC
            LIMIT 5
        """)
        result = await session.execute(stmt, {"since": since})
        rows = result.all()

        return [
            {
                "id": str(r[0]),
                "type": r[1],
                "message": r[2],
                "time": r[3].isoformat()
            }
            for r in rows
        ]

# Global Instance
health_service = HealthService()
