from __future__ import annotations
from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import SystemSetting
from typing import Dict, Any

class ClientSettingsController(Controller):
    """Elite V2.2: Public Settings Controller for Client Storefront."""
    path = "/api/v1/client/settings"

    @get("/primary")
    async def get_primary_config(self, db_session: AsyncSession) -> Dict[str, Any]:
        """PUBLIC: Lấy cấu hình chung (Primary Config) cho Storefront."""
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await db_session.execute(stmt)
        setting = result.scalar_one_or_none()

        # Fallback nếu chưa có dữ liệu trong DB
        default_config = {
            "site_name": "Micsmo Elite",
            "slogan": "Bật tông trắng sáng",
            "description": "Nền tảng mỹ phẩm Elite hàng đầu Việt Nam. Trải nghiệm mua sắm thông minh với công nghệ Agentic AI 2026.",
            "contact": {
                "hotline": "1800-MICSMO",
                "phone": "0949 901 122",
                "email": "legal@micsmo.com",
                "address": "Bitexco Financial Tower, Quận 1, TP. Hồ Chí Minh"
            }
        }

        return setting.value if setting else default_config
