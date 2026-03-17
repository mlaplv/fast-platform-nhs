import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.health import AnomalyResponse, AnomalyItem

logger = logging.getLogger("api-gateway")

class HealthService:
    @staticmethod
    async def get_system_anomalies(db_session: AsyncSession) -> AnomalyResponse:
        """
        Fetch recent anomalies for XoHi Agent reporting. R1.5: Zero-Hydration.
        """
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
        result = await db_session.execute(stmt, {"since": since})
        rows = result.all()
        anomalies = [
            AnomalyItem(id=str(r[0]), type=r[1], message=r[2], time=r[3].isoformat())
            for r in rows
        ]

        return AnomalyResponse(
            status="success",
            count=len(anomalies),
            anomalies=anomalies
        )

health_service = HealthService()
