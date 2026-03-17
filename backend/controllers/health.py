from __future__ import annotations
from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession
from backend.guards import PermissionGuard
from backend.schemas.health import HealthStatusResponse, AnomalyResponse
from backend.services.health_service import health_service

class HealthController(Controller):
    path = "/api/v1/health"

    @get("/")
    async def health_check(self) -> HealthStatusResponse:
        return HealthStatusResponse()

    @get("/anomalies", guards=[PermissionGuard("system:all")])
    async def get_system_anomalies(self, db_session: "AsyncSession") -> AnomalyResponse:
        """
        Fetch recent anomalies for XoHi Agent reporting.
        """
        return await health_service.get_system_anomalies(db_session)
