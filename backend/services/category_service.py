import uuid
from typing import List, Dict, Optional, Union, Sequence, cast
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest

logger = logging.getLogger("api-gateway")

class CategoryService:
    """
    ULTRA-LEAN CATEGORY SERVICE (ELITE V2.2)
    ----------------------------------------
    Handles all category-related logic and product count aggregation.
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
    """

    async def list_categories(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, object]]:
        """List root categories with children via Scalar Projection (Zero-Hydration)."""

        # Fetch all active categories in one go for efficient tree building
        stmt = text("""
            SELECT id, name, slug, parent_id, created_at
            FROM categories
            WHERE deleted_at IS NULL
            ORDER BY created_at ASC
        """)
        res = await session.execute(stmt)
        rows = res.all()

        # Build ID mapping and find product counts
        cat_map: Dict[str, Dict[str, object]] = {}
        all_ids: List[str] = []

        for r in rows:
            uid = str(r[0])
            all_ids.append(uid)
            cat_map[uid] = {
                "id": uid,
                "name": r[1],
                "slug": r[2],
                "parentId": str(r[3]) if r[3] else None,
                "productCount": 0,
                "children": [],
                "createdAt": r[4].isoformat() if r[4] else ""
            }

        # N+1 KILL: Batch product counts
        if all_ids:
            count_query = text("""
                SELECT category_id, COUNT(*)::int
                FROM product_bases
                WHERE category_id = ANY(:ids) AND deleted_at IS NULL
                GROUP BY category_id
            """)
            counts = await session.execute(count_query, {"ids": all_ids})
            for c_row in counts:
                cid = str(c_row[0])
                if cid in cat_map:
                    cat_map[cid]["productCount"] = c_row[1]

        # Assemble tree
        root_categories = []
        for cat in cat_map.values():
            p_id = cast(Optional[str], cat["parentId"])
            if p_id is None:
                root_categories.append(cat)
            elif p_id in cat_map:
                cast(List, cat_map[p_id]["children"]).append(cat)

        return root_categories[offset : offset + limit]

    async def create_category(self, session: AsyncSession, data: CreateCategoryRequest) -> Dict[str, object]:
        """Create a new category via Scalar Insert (Zero-Hydration)."""
        new_id = str(uuid.uuid4())
        slug = data.slug or data.name.lower().replace(" ", "-")

        await session.execute(
            text("""
                INSERT INTO categories (id, name, slug, parent_id, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :slug, :parent, 'default', NOW(), NOW())
            """),
            {
                "id": new_id,
                "name": data.name,
                "slug": slug,
                "parent": data.parentId
            }
        )
        await session.commit()

        return {
            "id": new_id,
            "name": data.name,
            "slug": slug,
            "parentId": data.parentId
        }

    async def update_category(self, session: AsyncSession, category_id: str, data: UpdateCategoryRequest) -> Dict[str, object]:
        """Update a category via direct SQL (Zero-Hydration)."""
        # Check existence
        sql_check = text("SELECT name, slug, parent_id FROM categories WHERE id = :id AND deleted_at IS NULL")
        res = await session.execute(sql_check, {"id": category_id})
        current = res.first()
        if not current:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Category {category_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return {"id": category_id, "message": "No changes"}

        set_clauses = []
        params = {"id": category_id}
        for key, value in update_data.items():
            db_col = key
            if key == "parentId": db_col = "parent_id"
            set_clauses.append(f"{db_col} = :{key}")
            params[key] = value

        set_clauses.append("updated_at = NOW()")
        sql = text(f"UPDATE categories SET {', '.join(set_clauses)} WHERE id = :id")
        await session.execute(sql, params)
        await session.commit()

        # Fetch updated state
        res_info = await session.execute(text("SELECT name, slug, parent_id FROM categories WHERE id = :id"), {"id": category_id})
        r = res_info.first()

        return {
            "id": category_id,
            "name": r[0] if r else "",
            "slug": r[1] if r else "",
            "parentId": str(r[2]) if r and r[2] else None
        }

    async def delete_categories(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete categories via Raw SQL."""
        stmt = text("UPDATE categories SET deleted_at = NOW() WHERE id = ANY(:ids)")
        result = await session.execute(stmt, {"ids": ids})
        await session.commit()
        return result.rowcount

# Global Instance
category_service = CategoryService()
