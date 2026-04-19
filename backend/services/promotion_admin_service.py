from typing import Optional, List
from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.promotion import Voucher
from backend.schemas.promotion import CreateVoucherRequest, UpdateVoucherRequest, VoucherListResponse, VoucherResponse
from backend.schemas.common import SuccessResponse
from backend.database import current_tenant_id
from litestar.exceptions import NotFoundException, ClientException

class PromotionAdminService:
    async def list_vouchers(
        self, 
        db_session: AsyncSession, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> VoucherListResponse:
        tenant_id = current_tenant_id.get() or "default"
        stmt = select(Voucher).where(Voucher.tenant_id == tenant_id)
        
        if search:
            stmt = stmt.where(Voucher.id.ilike(f"%{search}%"))
        if is_active is not None:
            stmt = stmt.where(Voucher.is_active == is_active)
            
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db_session.execute(count_stmt)).scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(Voucher.created_at.desc()).limit(limit).offset(offset)
        result = await db_session.execute(stmt)
        vouchers = result.scalars().all()
        
        return VoucherListResponse(
            data=[VoucherResponse.model_validate(v) for v in vouchers],
            total=total
        )

    async def create_voucher(self, db_session: AsyncSession, data: CreateVoucherRequest) -> SuccessResponse:
        tenant_id = current_tenant_id.get() or "default"
        
        # Check if code already exists
        existing = await db_session.get(Voucher, data.id)
        if existing:
            raise ClientException(status_code=409, detail=f"Mã voucher '{data.id}' đã tồn tại.")
        
        new_voucher = Voucher(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        db_session.add(new_voucher)
        await db_session.commit()
        return     SuccessResponse(message=f"Đã tạo voucher {data.id} thành công.")

    async def update_voucher(self, db_session: AsyncSession, voucher_id: str, data: UpdateVoucherRequest) -> SuccessResponse:
        voucher = await db_session.get(Voucher, voucher_id)
        if not voucher:
            raise NotFoundException(f"Voucher {voucher_id} không tồn tại.")
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(voucher, key, value)
            
        await db_session.commit()
        return SuccessResponse(message=f"Đậm cập nhật voucher {voucher_id} thành công.")

    async def delete_voucher(self, db_session: AsyncSession, voucher_id: str) -> SuccessResponse:
        voucher = await db_session.get(Voucher, voucher_id)
        if not voucher:
            raise NotFoundException(f"Voucher {voucher_id} không tồn tại.")
            
        await db_session.delete(voucher)
        await db_session.commit()
        return SuccessResponse(message=f"Đã xoá voucher {voucher_id} thành công.")

    async def bulk_delete_vouchers(self, db_session: AsyncSession, ids: List[str]) -> SuccessResponse:
        if not ids:
            return SuccessResponse(message="Không có voucher nào được chọn.")
        
        tenant_id = current_tenant_id.get() or "default"
        stmt = delete(Voucher).where(and_(Voucher.id.in_(ids), Voucher.tenant_id == tenant_id))
        await db_session.execute(stmt)
        await db_session.commit()
        return SuccessResponse(message=f"Đã xoá {len(ids)} voucher thành công.")

    async def bulk_update_status(self, db_session: AsyncSession, ids: List[str], is_active: bool) -> SuccessResponse:
        if not ids:
            return SuccessResponse(message="Không có voucher nào được chọn.")
        
        tenant_id = current_tenant_id.get() or "default"
        stmt = update(Voucher).where(and_(Voucher.id.in_(ids), Voucher.tenant_id == tenant_id)).values(is_active=is_active)
        await db_session.execute(stmt)
        await db_session.commit()
        return SuccessResponse(message=f"Đã cập nhật trạng thái cho {len(ids)} voucher thành công.")

promotion_admin_service = PromotionAdminService()
