import logging
from typing import Optional
from litestar import Controller, get, post, put, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.banner_service import banner_service
from backend.schemas.banner import CreateBannerRequest, UpdateBannerRequest, BannerResponse, BannerListResponse
from backend.schemas.common import SuccessResponse
from backend.database.models import Banner
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class BannerController(Controller):
    path = "/api/v1/banners"
    tags = ["Banners"]
    guards = [PermissionGuard(PermissionEnum.CONTENT_WRITE)]

    @get("/")
    async def list_banners(self, db_session: AsyncSession, position: Optional[str] = None, active_only: bool = False, limit: int = 100, offset: int = 0) -> BannerListResponse:
        """List banners with filters."""
        return await banner_service.list_banners(db_session, position, active_only, limit, offset)

    @post("/")
    async def create_banner(self, db_session: AsyncSession, data: CreateBannerRequest) -> SuccessResponse:
        """Create a new banner."""
        return await banner_service.create_banner(db_session, data)

    @put("/{banner_id:str}")
    async def update_banner(self, db_session: AsyncSession, banner_id: str, data: UpdateBannerRequest) -> SuccessResponse:
        """Update an existing banner."""
        return await banner_service.update_banner(db_session, banner_id, data)

    @delete("/{banner_id:str}", status_code=200)
    async def delete_banner(self, db_session: AsyncSession, banner_id: str) -> SuccessResponse:
        """Delete a banner."""
        return await banner_service.delete_banner(db_session, banner_id)
