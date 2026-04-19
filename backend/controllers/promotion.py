import logging
from typing import Optional
from litestar import Controller, get, post, patch, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.promotion_admin_service import promotion_admin_service
from backend.schemas.promotion import CreateVoucherRequest, UpdateVoucherRequest, VoucherListResponse
from backend.schemas.common import SuccessResponse
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class PromotionController(Controller):
    path = "/api/v1/admin/vouchers"
    tags = ["Admin Promotions"]
    guards = [PermissionGuard(PermissionEnum.CONTENT_WRITE)]

    @get("/")
    async def list_vouchers(
        self, 
        db_session: AsyncSession, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> VoucherListResponse:
        """List all vouchers with optional filters."""
        return await promotion_admin_service.list_vouchers(db_session, search, is_active, category, limit, offset)

    @post("/")
    async def create_voucher(self, db_session: AsyncSession, data: CreateVoucherRequest) -> SuccessResponse:
        """Create a new voucher."""
        return await promotion_admin_service.create_voucher(db_session, data)

    @patch("/{voucher_id:str}")
    async def update_voucher(self, db_session: AsyncSession, voucher_id: str, data: UpdateVoucherRequest) -> SuccessResponse:
        """Update an existing voucher."""
        return await promotion_admin_service.update_voucher(db_session, voucher_id, data)

    @delete("/{voucher_id:str}", status_code=200)
    async def delete_voucher(self, db_session: AsyncSession, voucher_id: str) -> SuccessResponse:
        """Delete a voucher."""
        return await promotion_admin_service.delete_voucher(db_session, voucher_id)

    @post("/bulk-delete")
    async def bulk_delete_vouchers(self, db_session: AsyncSession, data: dict) -> SuccessResponse:
        """Delete multiple vouchers."""
        voucher_ids = data.get("ids", [])
        return await promotion_admin_service.bulk_delete_vouchers(db_session, voucher_ids)

    @post("/bulk-status")
    async def bulk_update_status(self, db_session: AsyncSession, data: dict) -> SuccessResponse:
        """Update status for multiple vouchers."""
        voucher_ids = data.get("ids", [])
        is_active = data.get("is_active")
        is_default = data.get("is_default")
        return await promotion_admin_service.bulk_update_status(db_session, voucher_ids, is_active, is_default)
