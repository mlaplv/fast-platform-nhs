import logging
import uuid
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Tuple
from sqlalchemy import select, update, text, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.product import CreateProductRequest, UpdateProductRequest
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class ProductService:
    """
    ULTRA-LEAN PRODUCT SERVICE (ELITE V2.2)
    ---------------------------------------
    Handles all product-related logic, including pgvector embeddings.
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
    """

    async def list_products(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List products with total count and category projection via Scalar Projection (Zero-Hydration)."""
        conditions = ["p.deleted_at IS NULL"]
        params = {"limit": limit, "offset": offset}

        if status and status != "all":
            conditions.append("p.status = :status")
            params["status"] = status.upper()
        if search:
            conditions.append("(p.name ILIKE :search OR p.sku ILIKE :search)")
            params["search"] = f"%{escape_like(search)}%"

        where_clause = " AND ".join(conditions)

        # 1. COUNT (Zero-Hydration)
        count_sql = text(f"SELECT COUNT(*) FROM product_bases p WHERE {where_clause}")
        total = await session.scalar(count_sql, params) or 0

        # 2. Scalar Projection Fetch
        sql = text(f"""
            SELECT p.id, p.name, p.sku, p.price, p.stock, p.status, p.category_id, p.description, p.type, p.created_at, c.name as category_name
            FROM product_bases p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {where_clause}
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(sql, params)
        rows = result.all()

        data = [
            {
                "id": str(r[0]),
                "name": r[1],
                "sku": r[2] or "",
                "price": float(r[3]) if r[3] else 0.0,
                "stock": r[4],
                "status": r[5].lower() if r[5] else "draft",
                "category": r[10] or "",
                "categoryId": str(r[6]) if r[6] else None,
                "description": r[7],
                "type": r[8],
                "createdAt": r[9].isoformat() if r[9] else "",
            }
            for r in rows
        ]
        return {"data": data, "total": total}

    async def create_product(self, session: AsyncSession, data: CreateProductRequest) -> Dict[str, object]:
        """Create a new product via Scalar Insert (Zero-Hydration) and generate its embedding."""
        new_id = str(uuid.uuid4())

        await session.execute(
            text("""
                INSERT INTO product_bases (id, name, sku, price, stock, status, description, category_id, type, created_at, updated_at, tenant_id)
                VALUES (:id, :name, :sku, :price, :stock, :status, :desc, :cat_id, :type, NOW(), NOW(), 'default')
            """),
            {
                "id": new_id,
                "name": data.name,
                "sku": data.sku,
                "price": data.price,
                "stock": data.stock,
                "status": data.status.upper(),
                "desc": data.description,
                "cat_id": data.categoryId,
                "type": data.type
            }
        )

        # RAG: Generate embedding
        await self._upsert_embedding(session, new_id, data.name, data.description)

        await session.commit()
        return {
            "id": new_id,
            "name": data.name,
            "sku": data.sku,
            "price": data.price,
            "stock": data.stock,
            "status": data.status.lower(),
            "message": "Product created successfully"
        }

    async def update_product(self, session: AsyncSession, product_id: str, data: UpdateProductRequest) -> Dict[str, object]:
        """Update a product via direct SQL and refresh its embedding if necessary."""
        # Check existence first via scalar
        exists = await session.scalar(text("SELECT 1 FROM product_bases WHERE id = :id"), {"id": product_id})
        if not exists:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Product {product_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return {"id": product_id, "message": "No changes requested"}

        set_clauses = []
        params = {"id": product_id}
        for key, value in update_data.items():
            db_key = key
            if key == "categoryId": db_key = "category_id"

            set_clauses.append(f"{db_key} = :{key}")
            if key == "status":
                params[key] = value.upper()
            else:
                params[key] = value

        set_clauses.append("updated_at = NOW()")
        sql = text(f"UPDATE product_bases SET {', '.join(set_clauses)} WHERE id = :id")
        await session.execute(sql, params)

        # RAG: Update embedding if relevant fields changed
        if "name" in update_data or "description" in update_data:
            # Fetch current values for embedding
            current = await session.execute(
                text("SELECT name, description FROM product_bases WHERE id = :id"),
                {"id": product_id}
            )
            r = current.first()
            if r:
                await self._upsert_embedding(session, product_id, r[0], r[1])

        await session.commit()
        return {
            "id": product_id,
            "message": "Product updated successfully"
        }

    async def delete_products(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete multiple products via Raw SQL (Rule 1.5)."""
        sql = text("UPDATE product_bases SET deleted_at = NOW() WHERE id = ANY(:ids)")
        result = await session.execute(sql, {"ids": ids})
        await session.commit()
        return result.rowcount

    async def bulk_activate(self, session: AsyncSession, ids: List[str]) -> int:
        """Activate multiple products via Raw SQL."""
        sql = text("UPDATE product_bases SET status = 'ACTIVE', updated_at = NOW() WHERE id = ANY(:ids)")
        result = await session.execute(sql, {"ids": ids})
        await session.commit()
        return result.rowcount

    async def _upsert_embedding(self, session: AsyncSession, product_id: str, name: str, description: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding."""
        try:
            from backend.services.ai_engine.vector_memory import get_encoder
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
