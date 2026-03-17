from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.health_service import health_service
from backend.guards import PermissionGuard

class HealthController(Controller):
    path = "/api/v1/health"

    @get("/")
    async def health_check(self) -> dict:
        return {"system": "Fast-Platform Gateway", "status": "online"}

    @get("/anomalies", guards=[PermissionGuard("system:all")])
    async def get_system_anomalies(self, db_session: AsyncSession) -> dict:
        """
        Fetch recent anomalies for XoHi Agent reporting.
        """
        anomalies = await health_service.get_system_anomalies(db_session)

        return {
            "status": "success",
            "count": len(anomalies),
            "anomalies": anomalies
        }
