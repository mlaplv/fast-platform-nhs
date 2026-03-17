from __future__ import annotations
import logging
from typing import List, Dict, Union, Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import ProductBaseRepository, provide_product_repo
from backend.guards import PermissionGuard
from backend.schemas.product import CreateProductRequest, UpdateProductRequest, ProductResponse, ProductListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.services.product_service import product_service

logger = logging.getLogger("api-gateway")

class ProductController(Controller):
    """R2: Class-based Litestar Controller for Product CRUD."""
    path = "/api/v1/products"
    dependencies = {"prod_repo": Provide(provide_product_repo)}

    @get("/", guards=[PermissionGuard("product:read")])
    async def list_products(
        self, db_session: "AsyncSession",
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ProductListResponse:
        """List products (R76: Scalar Projection). R41: N+1 Safe."""
        return await product_service.list_products(db_session, limit, offset, status, search)

    @get("/{product_id:str}", guards=[PermissionGuard("product:read")])
    async def get_product(self, db_session: "AsyncSession", product_id: str) -> ProductResponse:
        """Get a single product (R76: Scalar Projection)."""
        return await product_service.get_product(db_session, product_id)

    @post("/", guards=[PermissionGuard("product:write")])
    async def create_product(self, db_session: "AsyncSession", data: CreateProductRequest) -> SuccessResponse:
        """Create a new product (Service-Centric RAG)."""
        res = await product_service.create_product(db_session, data)
        await db_session.commit()
        return res

    @patch("/{product_id:str}", guards=[PermissionGuard("product:write")])
    async def update_product(self, db_session: "AsyncSession", product_id: str, data: UpdateProductRequest) -> SuccessResponse:
        """Update a product (Service-Centric RAG)."""
        res = await product_service.update_product(db_session, product_id, data)
        await db_session.commit()
        return res

    @delete("/{product_id:str}", status_code=200, guards=[PermissionGuard("product:write")])
    async def delete_product(self, db_session: "AsyncSession", product_id: str) -> SuccessResponse:
        """R18: Soft delete."""
        res = await product_service.delete_product(db_session, product_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard("product:write")])
    async def bulk_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """R18: Soft delete multiple products."""
        res = await product_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-activate", guards=[PermissionGuard("product:write")])
    async def bulk_activate(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """Activate multiple products."""
        res = await product_service.bulk_activate(db_session, data.ids)
        await db_session.commit()
        return res
