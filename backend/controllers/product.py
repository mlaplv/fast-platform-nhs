from datetime import datetime, timezone
import uuid
import logging
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select
from sqlalchemy.orm import selectinload

from backend.database.repositories import ProductBaseRepository, provide_product_repo
from backend.database.models import ProductBase
from backend.guards import PermissionGuard
from backend.utils.sql import escape_like
from backend.schemas.product import CreateProductRequest, UpdateProductRequest
from backend.schemas.article import BulkIdsRequest

logger = logging.getLogger("api-gateway")

class ProductController(Controller):
    """R2: Class-based Litestar Controller for Product CRUD."""
    path = "/api/v1/products"
    dependencies = {"prod_repo": Provide(provide_product_repo)}

    @get("/", guards=[PermissionGuard("product:read")])
    async def list_products(
        self, prod_repo: ProductBaseRepository, 
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List products (R76: Scalar Projection). R41: N+1 Safe."""
        from sqlalchemy import func, and_, or_
        from backend.database.models import Category
        
        conditions = [ProductBase.deleted_at == None]
        if status and status != "all":
            conditions.append(ProductBase.status == status.upper())
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                func.unaccent(ProductBase.name).ilike(f"%{func.unaccent(safe)}%"),
                ProductBase.sku.ilike(f"%{safe}%"),
            ))

        # 1. COUNT (Zero-Hydration — Rule 1.5)
        count_stmt = select(func.count(ProductBase.id)).where(and_(*conditions))
        total = await prod_repo.session.scalar(count_stmt) or 0

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
        
        result = await prod_repo.session.execute(stmt)
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

    @post("/", guards=[PermissionGuard("product:write")])
    async def create_product(self, prod_repo: ProductBaseRepository, data: CreateProductRequest) -> Dict[str, object]:
        """Create a new product using repository."""
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
        await prod_repo.add(product)
        
        # RAG: Generate embedding using repo session
        await self._upsert_embedding(prod_repo, new_id, data.name, data.description)
        
        await prod_repo.session.commit()
        
        return {
            "id": new_id,
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
    async def update_product(self, prod_repo: ProductBaseRepository, product_id: str, data: UpdateProductRequest) -> Dict[str, object]:
        """Update a product using direct SQLAlchemy."""
        stmt = select(ProductBase).where(ProductBase.id == product_id).options(selectinload(ProductBase.category))
        result = await prod_repo.session.execute(stmt)
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
            await self._upsert_embedding(prod_repo, product_id, product.name, product.description)
            
        await prod_repo.session.commit()
        
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
    async def delete_product(self, prod_repo: ProductBaseRepository, product_id: str) -> dict:
        """R18: Soft delete using repository."""
        stmt = update(ProductBase).where(ProductBase.id == product_id).values(deleted_at=datetime.now(timezone.utc))
        await prod_repo.session.execute(stmt)
        await prod_repo.session.commit()
        return {"ok": True, "id": product_id}

    @post("/bulk-delete", guards=[PermissionGuard("product:write")])
    async def bulk_delete(self, prod_repo: ProductBaseRepository, data: BulkIdsRequest) -> dict:
        """R18: Soft delete multiple products. R39: Batch via update."""
        stmt = update(ProductBase).where(ProductBase.id.in_(data.ids)).values(deleted_at=datetime.now(timezone.utc))
        await prod_repo.session.execute(stmt)
        await prod_repo.session.commit()
        return {"ok": True, "deleted": len(data.ids)}

    @post("/bulk-activate", guards=[PermissionGuard("product:write")])
    async def bulk_activate(self, prod_repo: ProductBaseRepository, data: BulkIdsRequest) -> dict:
        """Activate multiple products using repository session."""
        stmt = update(ProductBase).where(ProductBase.id.in_(data.ids)).values(status="ACTIVE")
        await prod_repo.session.execute(stmt)
        await prod_repo.session.commit()
        return {"ok": True, "activated": len(data.ids)}

    async def _upsert_embedding(self, prod_repo: ProductBaseRepository, product_id: str, name: str, description: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding (R16)."""
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
            
            vector = embeddings[0].tolist()
            vector_str = "[" + ",".join(map(str, vector)) + "]"
            
            sql = text("""
                INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at)
                VALUES (:id, :product_id, :vector::vector, NOW(), NOW())
                ON CONFLICT (product_base_id) 
                DO UPDATE SET embedding = :vector::vector, updated_at = NOW();
            """)
            await prod_repo.session.execute(sql, {"id": str(uuid.uuid4()), "product_id": product_id, "vector": vector_str})
        except Exception as e:
            logger.error(f"[RAG] Embedding failed for {product_id}: {e}")
