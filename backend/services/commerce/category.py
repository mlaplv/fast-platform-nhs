import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, TypedDict
from pydantic import JsonValue
from collections import defaultdict

from sqlalchemy import text, select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import Category
from backend.schemas.category import CreateCategoryRequest, UpdateCategoryRequest, CategoryResponse, CategoryListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.services.event_bus import event_bus
from backend.utils.media import extract_media_urls

class CategoryNode(TypedDict, total=False):
    id: str
    name: str
    slug: str
    parent_id: Optional[str]
    description: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    image: Optional[str]
    created_at: datetime
    product_count: int
    children: List["CategoryNode"]

logger = logging.getLogger("api-gateway")

class CategoryService:
    @staticmethod
    async def list_categories(db_session: AsyncSession, limit: int = 100, offset: int = 0) -> CategoryListResponse:
        """Moves complex nested listing logic from CategoryController.list_categories. R1.5: Zero-Hydration."""
        # 1. Zero-Hydration Count
        count_stmt = select(func.count(Category.id)).where(
            Category.parent_id == None,
            Category.deleted_at == None
        )
        total = await db_session.scalar(count_stmt) or 0

        # 2. Optimized Fetch (Rule 1.5 - Scalar Projection / Zero-Hydration)
        stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.created_at
        ).where(
            Category.parent_id == None,
            Category.deleted_at == None
        ).order_by(Category.created_at.asc()).limit(limit).offset(offset)

        res = await db_session.execute(stmt)
        parent_rows = res.all()

        if not parent_rows:
            return CategoryListResponse(data=[], total=total)

        parent_ids = [str(r.id) for r in parent_rows]

        # Fetch children (Zero-Hydration)
        child_stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.created_at
        ).where(
            Category.parent_id.in_(parent_ids),
            Category.deleted_at == None
        ).order_by(Category.created_at.asc())

        child_res = await db_session.execute(child_stmt)
        child_rows = child_res.all()

        # N+1 KILL: Single raw SQL to get ALL product counts grouped by categoryId
        all_cat_ids = parent_ids + [str(r.id) for r in child_rows]

        count_map: Dict[str, int] = {}
        if all_cat_ids:
            query = text(
                'SELECT category_id, COUNT(*)::int as cnt FROM product_bases '
                'WHERE category_id = ANY(:ids) AND deleted_at IS NULL '
                'GROUP BY category_id'
            )
            rows = await db_session.execute(query, {"ids": all_cat_ids})
            count_map = {str(r[0]): r[1] for r in rows.all()}

        # 3. Data Construction (No ORM hydration)
        children_map: Dict[str, List[CategoryNode]] = defaultdict(list)
        for r in child_rows:
            c_dict: CategoryNode = dict(r._mapping) # type: ignore
            c_dict["product_count"] = count_map.get(str(r.id), 0)
            children_map[str(r.parent_id)].append(c_dict)

        data = []
        for r in parent_rows:
            p_dict: CategoryNode = dict(r._mapping) # type: ignore
            p_dict["product_count"] = count_map.get(str(r.id), 0)
            p_dict["children"] = children_map.get(str(r.id), [])
            data.append(CategoryResponse.model_validate(p_dict))

        return CategoryListResponse(data=data, total=total)

    @staticmethod
    async def create_category(db_session: AsyncSession, data: CreateCategoryRequest) -> SuccessResponse:
        """Moves logic from CategoryController.create_category."""
        new_id = str(uuid.uuid4())
        category = Category(
            id=new_id,
            name=data.name,
            slug=data.slug or data.name.lower().replace(" ", "-"),
            parent_id=data.parentId,
            description=data.description,
            seo_title=data.seoTitle,
            seo_description=data.seoDescription,
            image=data.image,
        )
        db_session.add(category)
        await db_session.commit()
        
        # Elite V2.2: Sync Media
        await CategoryService._sync_media_links(new_id, data.image)
        
        return SuccessResponse(ok=True, id=new_id)

    @staticmethod
    async def update_category(db_session: AsyncSession, category_id: str, data: UpdateCategoryRequest) -> SuccessResponse:
        """Moves logic from CategoryController.update_category."""
        stmt = select(Category).where(Category.id == category_id)
        res = await db_session.execute(stmt)
        category = res.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        if data.name is not None: category.name = data.name
        if data.slug is not None: category.slug = data.slug
        if data.parentId is not None: category.parent_id = data.parentId
        if data.description is not None: category.description = data.description
        if data.seoTitle is not None: category.seo_title = data.seoTitle
        if data.seoDescription is not None: category.seo_description = data.seoDescription
        if data.image is not None: category.image = data.image

        category.updated_at = datetime.now(timezone.utc)
        await db_session.commit()
        
        # Elite V2.2: Sync Media
        await CategoryService._sync_media_links(category_id, category.image)

        return SuccessResponse(ok=True, id=category_id)

    @staticmethod
    async def delete_category(db_session: AsyncSession, category_id: str) -> SuccessResponse:
        """Moves logic from CategoryController.delete_category."""
        stmt = select(Category).where(Category.id == category_id)
        res = await db_session.execute(stmt)
        category = res.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        category.deleted_at = datetime.now(timezone.utc)
        return SuccessResponse(ok=True, id=category_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        """Moves logic from CategoryController.bulk_delete."""
        stmt = update(Category).where(Category.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def _sync_media_links(category_id: str, image_url: Optional[str]) -> None:
        """Phát sự kiện đồng bộ Media cho Category."""
        try:
            urls = extract_media_urls(image_url)
            if urls:
                await event_bus.emit("MEDIA_SYNC_REQUIRED", {
                    "entity_id": category_id,
                    "entity_type": "category",
                    "urls": list(urls)
                })
                logger.info(f"[CategoryService] Emitted MEDIA_SYNC_REQUIRED for category {category_id}")
        except Exception as e:
            logger.error(f"[CategoryService] Failed to emit media sync: {e}")

category_service = CategoryService()
