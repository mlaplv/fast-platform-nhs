from __future__ import annotations
from litestar import Controller, get, post, patch, delete, Request
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest, CategoryResponse, CategoryListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest, BulkStatusRequest
from backend.services.commerce.category import category_service

class CategoryController(Controller):
    """R2: Class-based Litestar Controller for Category CRUD."""
    path = "/api/v1/categories"
    guards = [PermissionGuard(PermissionEnum.CATEGORY_READ)]

    @get("/", guards=[PermissionGuard(PermissionEnum.CATEGORY_READ)])
    async def list_categories(self, db_session: "AsyncSession", limit: int = 100, offset: int = 0) -> CategoryListResponse:
        """List root categories with children + product counts. R41: N+1 Safe. R1.5: Zero-Hydration."""
        return await category_service.list_categories(db_session, limit, offset)

    @post("/", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def create_category(self, db_session: "AsyncSession", data: CreateCategoryRequest) -> SuccessResponse:
        """Create a new category using repository."""
        res = await category_service.create_category(db_session, data)
        await db_session.commit()
        return res

    @patch("/{category_id:str}", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def update_category(self, db_session: "AsyncSession", category_id: str, data: UpdateCategoryRequest) -> SuccessResponse:
        """Update a category using repository."""
        res = await category_service.update_category(db_session, category_id, data)
        await db_session.commit()
        return res

    @delete("/{category_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def delete_category(self, db_session: "AsyncSession", category_id: str) -> SuccessResponse:
        """R18: Soft delete using repository."""
        res = await category_service.delete_category(db_session, category_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def bulk_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """R18: Soft delete mú hàng loạt. Guard: bỏ qua ID có sản phẩm/con, trả về danh sách skipped."""
        res = await category_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/hard-delete", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def hard_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> SuccessResponse:
        """Xóa vĩnh viễn 1 danh mục. Guard: Từ chối nếu có sản phẩm hoặc danh mục con."""
        res = await category_service.hard_delete_category(db_session, data.ids[0])
        await db_session.commit()
        return res

    @post("/bulk-hard-delete", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def bulk_hard_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """Xóa vĩnh viễn hàng loạt. Guard: bỏ qua ID có sản phẩm/con, trả về danh sách skipped."""
        res = await category_service.bulk_hard_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-status", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def bulk_status(self, db_session: "AsyncSession", data: BulkStatusRequest) -> BulkActionResponse:
        """Elite V2.2: Batch update category status (active/deactive)."""
        res = await category_service.bulk_update_status(db_session, data.ids, data.active)
        await db_session.commit()
        return res

    @patch("/reorder", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def reorder_categories(self, db_session: "AsyncSession", data: BulkIdsRequest) -> SuccessResponse:
        """Cập nhật thứ tự hiển thị danh mục theo danh sách ID."""
        return await category_service.reorder_categories(db_session, data.ids)

    @post("/seo-suggest", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def suggest_seo(self, data: Dict[str, str]) -> Dict[str, str]:
        """Elite V2.2: AI SEO Suggestion for Categories."""
        name = data.get("name", "")
        description = data.get("description", "")
        # Gọi ProductService logic tương tự vì metadata SEO giống nhau
        from backend.services.commerce.product import provide_product_service, ProductVectorService
        ps = await provide_product_service(vector_service=None) # type: ignore
        return await ps.suggest_seo(name, description)

    @post("/faq-suggest", guards=[PermissionGuard(PermissionEnum.CATEGORY_WRITE)])
    async def suggest_faqs(self, data: Dict[str, str]) -> List[Dict[str, str]]:
        """Elite V2.2: AI FAQ Generation for Categories."""
        name = data.get("name", "")
        description = data.get("description", "")
        from backend.services.commerce.product import provide_product_service
        ps = await provide_product_service(vector_service=None) # type: ignore
        return await ps.suggest_faqs(name, description)
