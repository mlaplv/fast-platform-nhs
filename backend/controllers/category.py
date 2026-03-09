from datetime import datetime, timezone
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

from backend.database.repositories import CategoryRepository, provide_category_repo
from backend.database.models import Category
from backend.guards import PermissionGuard
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest
from backend.schemas.article import BulkIdsRequest

class CategoryController(Controller):
    """R2: Class-based Litestar Controller for Category CRUD."""
    path = "/api/v1/categories"
    dependencies = {"cat_repo": Provide(provide_category_repo)}

    @get("/", guards=[PermissionGuard("category:read")])
    async def list_categories(self, cat_repo: CategoryRepository, limit: int = 100, offset: int = 0) -> List[Dict[str, object]]:
        """List root categories with children + product counts. N+1 KILLED via raw SQL batch."""
        
        # AdvancedAlchemy repository can handle the basic list. 
        # For complex root-only logic, we still use the repo's session if needed, 
        # but we use cat_repo.list where possible.
        # Optimized Fetch (Rule R41 - N+1 Safe with selectinload for children)
        stmt = select(Category).where(
            Category.parent_id == None,
            Category.deleted_at == None
        ).options(selectinload(Category.children)).order_by(Category.created_at.asc()).limit(limit).offset(offset)
        
        res = await cat_repo.session.execute(stmt)
        categories = res.scalars().all()

        # N+1 KILL: Single raw SQL to get ALL product counts grouped by categoryId
        all_cat_ids = []
        for cat in categories:
            all_cat_ids.append(str(cat.id))
            for child in (getattr(cat, "children", []) or []):
                all_cat_ids.append(str(child.id))

        count_map: Dict[str, int] = {}
        if all_cat_ids:
            # R19: Standard SQL for counts - still valid via repo.session
            query = text(
                'SELECT category_id, COUNT(*)::int as cnt FROM product_bases '
                'WHERE category_id = ANY(:ids) AND deleted_at IS NULL '
                'GROUP BY category_id'
            )
            rows = await cat_repo.session.execute(query, {"ids": all_cat_ids})
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

    @post("/", guards=[PermissionGuard("category:write")])
    async def create_category(self, cat_repo: CategoryRepository, data: CreateCategoryRequest) -> Dict[str, object]:
        """Create a new category using repository."""
        category = Category(
            name=data.name,
            slug=data.slug or data.name.lower().replace(" ", "-"),
            parent_id=data.parentId,
        )
        created = await cat_repo.add(category)
        await cat_repo.session.commit()
        
        return {
            "id": str(created.id), "name": created.name, "slug": created.slug,
            "parentId": str(created.parent_id) if created.parent_id else None, 
            "productCount": 0,
            "children": [], "createdAt": created.created_at.isoformat() if created.created_at else "",
        }

    @patch("/{category_id:str}", guards=[PermissionGuard("category:write")])
    async def update_category(self, cat_repo: CategoryRepository, category_id: str, data: UpdateCategoryRequest) -> Dict[str, object]:
        """Update a category using repository."""
        category = await cat_repo.get(category_id)
        
        if data.name is not None: category.name = data.name
        if data.slug is not None: category.slug = data.slug
        if data.parentId is not None: category.parent_id = data.parentId
        
        await cat_repo.session.commit()
        return {"id": str(category.id), "name": category.name, "slug": category.slug}

    @delete("/{category_id:str}", status_code=200, guards=[PermissionGuard("category:write")])
    async def delete_category(self, cat_repo: CategoryRepository, category_id: str) -> dict:
        """R18: Soft delete using repository."""
        category = await cat_repo.get(category_id)
        category.deleted_at = datetime.now(timezone.utc)
        await cat_repo.session.commit()
        return {"ok": True, "id": category_id}

    @post("/bulk-delete", guards=[PermissionGuard("category:write")])
    async def bulk_delete(self, cat_repo: CategoryRepository, data: BulkIdsRequest) -> dict:
        """R18: Soft delete multiple categories. R39: Batch via update."""
        from sqlalchemy import update
        stmt = update(Category).where(Category.id.in_(data.ids)).values(deleted_at=datetime.now(timezone.utc))
        await cat_repo.session.execute(stmt)
        await cat_repo.session.commit()
        return {"ok": True, "deleted": len(data.ids)}
