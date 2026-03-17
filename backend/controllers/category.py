from datetime import datetime, timezone
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Category
from backend.services.category_service import category_service
from backend.guards import PermissionGuard
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest
from backend.schemas.article import BulkIdsRequest

class CategoryController(Controller):
    """R2: Class-based Litestar Controller for Category CRUD."""
    path = "/api/v1/categories"

    @get("/", guards=[PermissionGuard("category:read")])
    async def list_categories(self, db_session: AsyncSession, limit: int = 100, offset: int = 0) -> List[Dict[str, object]]:
        """List root categories via CategoryService."""
        return await category_service.list_categories(
            session=db_session,
            limit=limit,
            offset=offset
        )

    @post("/", guards=[PermissionGuard("category:write")])
    async def create_category(self, db_session: AsyncSession, data: CreateCategoryRequest) -> Dict[str, object]:
        """Create a new category via CategoryService."""
        return await category_service.create_category(db_session, data)

    @patch("/{category_id:str}", guards=[PermissionGuard("category:write")])
    async def update_category(self, db_session: AsyncSession, category_id: str, data: UpdateCategoryRequest) -> Dict[str, object]:
        """Update a category via CategoryService."""
        return await category_service.update_category(db_session, category_id, data)

    @delete("/{category_id:str}", status_code=200, guards=[PermissionGuard("category:write")])
    async def delete_category(self, db_session: AsyncSession, category_id: str) -> dict:
        """Soft delete via CategoryService."""
        await category_service.delete_categories(db_session, [category_id])
        return {"ok": True, "id": category_id}

    @post("/bulk-delete", guards=[PermissionGuard("category:write")])
    async def bulk_delete(self, db_session: AsyncSession, data: BulkIdsRequest) -> dict:
        """Bulk soft delete via CategoryService."""
        count = await category_service.delete_categories(db_session, data.ids)
        return {"ok": True, "deleted": count}
