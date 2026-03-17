from datetime import datetime, timezone
import uuid
import logging
from litestar import Controller, get, post, patch, delete
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import ProductBase
from backend.services.product_service import product_service
from backend.guards import PermissionGuard
from backend.schemas.product import CreateProductRequest, UpdateProductRequest
from backend.schemas.article import BulkIdsRequest

logger = logging.getLogger("api-gateway")

class ProductController(Controller):
    """R2: Class-based Litestar Controller for Product CRUD."""
    path = "/api/v1/products"

    @get("/", guards=[PermissionGuard("product:read")])
    async def list_products(
        self, db_session: AsyncSession,
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List products (R76: Scalar Projection). R41: N+1 Safe."""
        return await product_service.list_products(
            session=db_session,
            limit=limit,
            offset=offset,
            status=status,
            search=search
        )

    @post("/", guards=[PermissionGuard("product:write")])
    async def create_product(self, db_session: AsyncSession, data: CreateProductRequest) -> Dict[str, object]:
        """Create a new product using service."""
        product = await product_service.create_product(db_session, data)

        return {
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku or "",
            "price": product.price,
            "stock": product.stock,
            "status": product.status.lower(),
            "category": "",
            "categoryId": str(product.category_id) if product.category_id else None,
            "description": product.description,
            "type": product.type,
            "createdAt": product.created_at.isoformat() if product.created_at else "",
        }

    @patch("/{product_id:str}", guards=[PermissionGuard("product:write")])
    async def update_product(self, db_session: AsyncSession, product_id: str, data: UpdateProductRequest) -> Dict[str, object]:
        """Update a product via service."""
        product = await product_service.update_product(db_session, product_id, data)

        return {
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku or "",
            "price": product.price,
            "stock": product.stock,
            "status": product.status.lower(),
            "category": product.category.name if product.category else "",
        }

    @delete("/{product_id:str}", status_code=200, guards=[PermissionGuard("product:write")])
    async def delete_product(self, db_session: AsyncSession, product_id: str) -> dict:
        """R18: Soft delete via service."""
        await product_service.delete_products(db_session, [product_id])
        return {"ok": True, "id": product_id}

    @post("/bulk-delete", guards=[PermissionGuard("product:write")])
    async def bulk_delete(self, db_session: AsyncSession, data: BulkIdsRequest) -> dict:
        """R18: Soft delete multiple products."""
        count = await product_service.delete_products(db_session, data.ids)
        return {"ok": True, "deleted": count}

    @post("/bulk-activate", guards=[PermissionGuard("product:write")])
    async def bulk_activate(self, db_session: AsyncSession, data: BulkIdsRequest) -> dict:
        """Activate multiple products via service."""
        count = await product_service.bulk_activate(db_session, data.ids)
        return {"ok": True, "activated": count}
