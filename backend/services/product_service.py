import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import ProductBase, Category
from backend.schemas.product import CreateProductRequest, UpdateProductRequest, ProductResponse, ProductListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse
from backend.services.product_vector_service import product_vector_service
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class ProductService:
    @staticmethod
    async def list_products(
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ProductListResponse:
        """List products (R76: Scalar Projection). R1.5: Zero-Hydration."""
        conditions = [ProductBase.deleted_at == None]
        if status and status != "all":
            conditions.append(ProductBase.status == status.upper())
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                func.unaccent(ProductBase.name).ilike(f"%{func.unaccent(safe)}%"),
                ProductBase.sku.ilike(f"%{safe}%"),
            ))

        # 1. COUNT (Zero-Hydration)
        count_stmt = select(func.count(ProductBase.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # 2. R76: Scalar Projection Fetch
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.description, ProductBase.type,
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(ProductBase.created_at.desc())

        result = await db_session.execute(stmt)
        data = [ProductResponse.model_validate(row._mapping) for row in result]
        return ProductListResponse(data=data, total=total)

    @staticmethod
    async def get_product(db_session: AsyncSession, product_id: str) -> ProductResponse:
        """Get a single product (R76: Scalar Projection)."""
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.description, ProductBase.type,
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            ProductBase.id == product_id,
            ProductBase.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Product {product_id} not found")

        return ProductResponse.model_validate(row._mapping)

    @staticmethod
    async def create_product(db_session: AsyncSession, data: CreateProductRequest) -> SuccessResponse:
        """Create a new product and its embedding."""
        new_id = str(uuid.uuid4())
        product = ProductBase(
            id=new_id,
            name=data.name,
            sku=data.sku,
            price=data.price,
            stock=data.stock,
            status=data.status.upper(),
            description=data.description,
            category_id=data.categoryId,
            type=data.type,
        )
        db_session.add(product)

        # RAG Upsert
        await product_vector_service.upsert_product_embedding(
            db_session, new_id, data.name, data.description
        )

        return SuccessResponse(ok=True, id=new_id)

    @staticmethod
    async def update_product(db_session: AsyncSession, product_id: str, data: UpdateProductRequest) -> SuccessResponse:
        """Update a product and its embedding."""
        # Rule 1.5: Detail fetch for update (Surgical)
        stmt = select(ProductBase).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
        result = await db_session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise NotFoundException(f"Product {product_id} not found")

        if data.name is not None: product.name = data.name
        if data.sku is not None: product.sku = data.sku
        if data.price is not None: product.price = data.price
        if data.stock is not None: product.stock = data.stock
        if data.status is not None: product.status = data.status.upper()
        if data.description is not None: product.description = data.description
        if data.categoryId is not None: product.category_id = data.categoryId

        if data.name is not None or data.description is not None:
            await product_vector_service.upsert_product_embedding(
                db_session, product_id, product.name, product.description
            )

        return SuccessResponse(ok=True, id=product_id)

    @staticmethod
    async def delete_product(db_session: AsyncSession, product_id: str) -> SuccessResponse:
        stmt = update(ProductBase).where(ProductBase.id == product_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=product_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def bulk_activate(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(status="ACTIVE")
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

product_service = ProductService()
