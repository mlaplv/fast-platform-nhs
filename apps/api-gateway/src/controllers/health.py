from litestar import Controller, get, Request
from litestar.exceptions import HTTPException
from sqlalchemy import select, text
from src.database import alchemy_config
from src.guards import PermissionGuard

class HealthController(Controller):
    path = "/api/v1/health"

    @get("/")
    async def health_check(self) -> dict:
        return {"system": "Fast-Platform Gateway", "status": "online"}

    @get("/anomalies", guards=[PermissionGuard("system:all")])
    async def get_system_anomalies(self, request: Request) -> dict:
        """
        Fetch recent anomalies for XoHi Agent reporting.
        """
        async with alchemy_config.create_session_maker()() as session:
            from datetime import datetime, timedelta, timezone
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
            anomalies = [
                {"id": r[0], "type": r[1], "message": r[2], "time": r[3].isoformat()}
                for r in rows
            ]
            
            return {
                "status": "success",
                "count": len(anomalies),
                "anomalies": anomalies
            }
