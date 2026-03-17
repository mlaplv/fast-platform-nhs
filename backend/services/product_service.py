import logging
import uuid
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Tuple
from sqlalchemy import select, update, text, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import ProductBase, Category
from backend.schemas.product import CreateProductRequest, UpdateProductRequest
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class ProductService:
    """
    ULTRA-LEAN PRODUCT SERVICE (ELITE V2.2)
    ---------------------------------------
    Handles all product-related logic, including pgvector embeddings.
    """

    async def list_products(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List products with total count and category projection."""
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
        total = await session.scalar(count_stmt) or 0

        # 2. Scalar Projection Fetch
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.description, ProductBase.type,
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(ProductBase.created_at.desc())

        result = await session.execute(stmt)
        data = [
            {
                "id": str(row.id),
                "name": row.name,
                "sku": row.sku or "",
                "price": row.price,
                "stock": row.stock,
                "status": row.status.lower() if row.status else "draft",
                "category": row.category_name or "",
                "categoryId": str(row.category_id) if row.category_id else None,
                "description": row.description,
                "type": row.type,
                "createdAt": row.created_at.isoformat() if row.created_at else "",
            }
            for row in result
        ]
        return {"data": data, "total": total}

    async def create_product(self, session: AsyncSession, data: CreateProductRequest) -> ProductBase:
        """Create a new product and generate its embedding."""
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
        session.add(product)

        # RAG: Generate embedding
        await self._upsert_embedding(session, new_id, data.name, data.description)

        await session.commit()
        return product

    async def update_product(self, session: AsyncSession, product_id: str, data: UpdateProductRequest) -> ProductBase:
        """Update a product and refresh its embedding if necessary."""
        stmt = select(ProductBase).where(ProductBase.id == product_id).options(selectinload(ProductBase.category))
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Product {product_id} not found")

        if data.name is not None: product.name = data.name
        if data.sku is not None: product.sku = data.sku
        if data.price is not None: product.price = data.price
        if data.stock is not None: product.stock = data.stock
        if data.status is not None: product.status = data.status.upper()
        if data.description is not None: product.description = data.description
        if data.categoryId is not None: product.category_id = data.categoryId

        # RAG: Update embedding
        if data.name is not None or data.description is not None:
            await self._upsert_embedding(session, product_id, product.name, product.description)

        await session.commit()
        return product

    async def delete_products(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete multiple products."""
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(
            deleted_at=datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    async def bulk_activate(self, session: AsyncSession, ids: List[str]) -> int:
        """Activate multiple products."""
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(status="ACTIVE")
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    async def _upsert_embedding(self, session: AsyncSession, product_id: str, name: str, description: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding."""
        try:
            from backend.services.ai_engine.core.vector_memory import get_encoder
            encoder = get_encoder()
            if not encoder:
                return

            content = f"{name} {description or ''}".strip()
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, lambda: list(encoder.embed([content])))
            if not embeddings:
                return

            vector = embeddings[0]
            vector_np = np.array(vector, dtype=np.float32)
            vector_hex = vector_np.tobytes().hex()

            sql = text("""
                INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at)
                VALUES (:id, :product_id, :vector, NOW(), NOW())
                ON CONFLICT (product_base_id)
                DO UPDATE SET embedding = :vector, updated_at = NOW();
            """)
            await session.execute(sql, {"id": str(uuid.uuid4()), "product_id": product_id, "vector": vector_hex})
        except Exception as e:
            logger.error(f"[RAG] Embedding failed for {product_id}: {e}")

# Global Instance
product_service = ProductService()
