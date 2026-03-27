from __future__ import annotations
from litestar import Controller, get, post, patch, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional

from backend.guards import PermissionGuard
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest, CategoryResponse, CategoryListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.services.commerce.category import category_service

class CategoryController(Controller):
    """R2: Class-based Litestar Controller for Category CRUD."""
    path = "/api/v1/categories"

    @get("/", guards=[PermissionGuard("category:read")])
    async def list_categories(self, db_session: "AsyncSession", limit: int = 100, offset: int = 0) -> CategoryListResponse:
        """List root categories with children + product counts. R41: N+1 Safe. R1.5: Zero-Hydration."""
        return await category_service.list_categories(db_session, limit, offset)

    @post("/", guards=[PermissionGuard("category:write")])
    async def create_category(self, db_session: "AsyncSession", data: CreateCategoryRequest) -> SuccessResponse:
        """Create a new category using repository."""
        res = await category_service.create_category(db_session, data)
        await db_session.commit()
        return res

    @patch("/{category_id:str}", guards=[PermissionGuard("category:write")])
    async def update_category(self, db_session: "AsyncSession", category_id: str, data: UpdateCategoryRequest) -> SuccessResponse:
        """Update a category using repository."""
        res = await category_service.update_category(db_session, category_id, data)
        await db_session.commit()
        return res

    @delete("/{category_id:str}", status_code=200, guards=[PermissionGuard("category:write")])
    async def delete_category(self, db_session: "AsyncSession", category_id: str) -> SuccessResponse:
        """R18: Soft delete using repository."""
        res = await category_service.delete_category(db_session, category_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard("category:write")])
    async def bulk_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """R18: Soft delete multiple categories. R39: Batch via update."""
        res = await category_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res
