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
        """PUBLIC: Lấy cấu hình chung (Primary Config) cho Storefront."""
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await db_session.execute(stmt)
        setting = result.scalar_one_or_none()

        # 1. Nếu có dữ liệu trong DB -> Parse sang Model
        if setting and setting.value:
            return SystemSettingsPayload.model_validate(setting.value)

        # 2. Fallback nếu chưa có dữ liệu (Elite V2.2)
        return SystemSettingsPayload(
            basic_info=BasicInfo(
                site_name="osmo Elite",
                description="Nền tảng mỹ phẩm Elite hàng đầu Việt Nam."
            ),
            contact_info=ContactInfo(
                hotline="1800-osmo",
                phone="0949 901 122",
                email="legal@osmo",
                address="Bitexco Financial Tower, Quận 1, TP. Hồ Chí Minh"
            )
        )

