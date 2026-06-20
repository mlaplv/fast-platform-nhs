from __future__ import annotations
from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import SystemSetting
from backend.schemas.system_settings import SystemSettingsPayload, BasicInfo, ContactInfo

class ClientSettingsController(Controller):
    """Elite V2.2: Public Settings Controller for Client Storefront."""
    path = "/api/v1/client/settings"

    @get("/primary")
    async def get_primary_config(self, db_session: AsyncSession) -> SystemSettingsPayload:
        """PUBLIC: Lấy cấu hình chung (Primary Config) cho Storefront (Cached)."""
        from backend.services.settings_service import SettingsService
        resp = await SettingsService.get_general_settings(db_session)
        return resp.settings

