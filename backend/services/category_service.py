import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Sequence
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Category
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest

logger = logging.getLogger("api-gateway")

class CategoryService:
    """
    ULTRA-LEAN CATEGORY SERVICE (ELITE V2.2)
    ----------------------------------------
    Handles all category-related logic and product count aggregation.
    """

    async def list_categories(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, object]]:
        """List root categories with children + product counts. N+1 KILLED via raw SQL batch."""

        stmt = select(Category).where(
            Category.parent_id == None,
            Category.deleted_at == None
        ).options(selectinload(Category.children)).order_by(Category.created_at.asc()).limit(limit).offset(offset)

        res = await session.execute(stmt)
        categories = res.scalars().all()

        # N+1 KILL: Single raw SQL to get ALL product counts grouped by categoryId
        all_cat_ids: List[str] = []
        for cat in categories:
            all_cat_ids.append(str(cat.id))
            for child in (getattr(cat, "children", []) or []):
                if child.deleted_at is None:
                    all_cat_ids.append(str(child.id))

        count_map: Dict[str, int] = {}
        if all_cat_ids:
            query = text(
                'SELECT category_id, COUNT(*)::int as cnt FROM product_bases '
                'WHERE category_id = ANY(:ids) AND deleted_at IS NULL '
                'GROUP BY category_id'
            )
            rows = await session.execute(query, {"ids": all_cat_ids})
            count_map = {str(r[0]): r[1] for r in rows.all()}

        result = []
        for cat in categories:
            children_data = [
                {
                    "id": str(child.id), "name": child.name, "slug": child.slug,
                    "parentId": str(child.parent_id) if child.parent_id else None,
                    "productCount": count_map.get(str(child.id), 0),
                    "children": [],
                    "createdAt": child.created_at.isoformat() if child.created_at else "",
                }
                for child in (getattr(cat, "children", []) or [])
                if child.deleted_at is None
            ]
            result.append({
                "id": str(cat.id), "name": cat.name, "slug": cat.slug,
                "parentId": str(cat.parent_id) if cat.parent_id else None,
                "productCount": count_map.get(str(cat.id), 0),
                "children": children_data,
                "createdAt": cat.created_at.isoformat() if cat.created_at else "",
            })
        return result

    async def create_category(self, session: AsyncSession, data: CreateCategoryRequest) -> Category:
        """Create a new category."""
        category = Category(
            name=data.name,
            slug=data.slug or data.name.lower().replace(" ", "-"),
            parent_id=data.parentId,
        )
        session.add(category)
        await session.commit()
        return category

    async def update_category(self, session: AsyncSession, category_id: str, data: UpdateCategoryRequest) -> Category:
        """Update a category."""
        category = await session.get(Category, category_id)
        if not category:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Category {category_id} not found")

        if data.name is not None: category.name = data.name
        if data.slug is not None: category.slug = data.slug
        if data.parentId is not None: category.parent_id = data.parentId

        await session.commit()
        return category

    async def delete_categories(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete categories."""
        stmt = update(Category).where(Category.id.in_(ids)).values(
            deleted_at=datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

# Global Instance
category_service = CategoryService()
