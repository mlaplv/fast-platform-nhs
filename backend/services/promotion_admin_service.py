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
        category: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> VoucherListResponse:
        tenant_id = current_tenant_id.get() or "default"
        stmt = select(Voucher).where(Voucher.tenant_id == tenant_id)
        
        if search:
            stmt = stmt.where(Voucher.id.ilike(f"%{search}%"))
        if is_active is not None:
            stmt = stmt.where(Voucher.is_active == is_active)
        if category:
            stmt = stmt.where(Voucher.category == category)
            
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
        
        # [ELITE V2.2] Handle voucher ID (code) change via Explicit SQL Update for PK integrity
        new_id = update_data.pop("id", None)
        if new_id and new_id != voucher_id:
            # Check if new ID already exists
            existing = await db_session.get(Voucher, new_id)
            if existing:
                raise ClientException(status_code=409, detail=f"Mã voucher '{new_id}' đã tồn tại.")
            
            # Use raw update to force PK change in DB
            await db_session.execute(
                update(Voucher).where(Voucher.id == voucher_id).values(id=new_id)
            )
            # Flush and re-fetch to update session identity map
            await db_session.flush()
            voucher = await db_session.get(Voucher, new_id)
            if not voucher:
                raise NotFoundException(f"Lỗi đồng bộ voucher {new_id} sau khi đổi mã.")
            
        is_setting_default = update_data.get("is_default", False)
        
        if is_setting_default:
            tenant_id = voucher.tenant_id
            category = update_data.get("category") or voucher.category
            # Unset all other defaults in same category
            await db_session.execute(
                update(Voucher)
                .where(and_(Voucher.tenant_id == tenant_id, Voucher.category == category, Voucher.id != (new_id or voucher_id)))
                .values(is_default=False)
            )

        for key, value in update_data.items():
            setattr(voucher, key, value)
            
        await db_session.commit()
        return SuccessResponse(message=f"Đã cập nhật voucher {new_id or voucher_id} thành công.")

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

    async def bulk_update_status(self, db_session: AsyncSession, ids: List[str], is_active: Optional[bool] = None, is_default: Optional[bool] = None) -> SuccessResponse:
        if not ids:
            return SuccessResponse(message="Không có voucher nào được chọn.")
        
        tenant_id = current_tenant_id.get() or "default"
        
        if is_active is not None:
            stmt = update(Voucher).where(and_(Voucher.id.in_(ids), Voucher.tenant_id == tenant_id)).values(is_active=is_active)
            await db_session.execute(stmt)
            
        if is_default is True:
            # For bulk setting default, we pick the LAST one in the list to be the absolute default per category
            # To be safe, we iterate through categories of selected vouchers
            stmt = select(Voucher).where(and_(Voucher.id.in_(ids), Voucher.tenant_id == tenant_id))
            vouchers = (await db_session.execute(stmt)).scalars().all()
            
            categories = set(v.category for v in vouchers)
            for cat in categories:
                # Unset all in category
                await db_session.execute(
                    update(Voucher).where(and_(Voucher.tenant_id == tenant_id, Voucher.category == cat)).values(is_default=False)
                )
                # Set the last one from our selection in this category to True
                last_in_cat = [v for v in vouchers if v.category == cat][-1]
                last_in_cat.is_default = True
        
        await db_session.commit()
        return SuccessResponse(message=f"Đã cập nhật hàng loạt {len(ids)} voucher thành công.")

promotion_admin_service = PromotionAdminService()
