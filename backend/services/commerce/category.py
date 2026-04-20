import uuid
import json
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
from backend.services.xohi_memory import xohi_memory
from backend.services.commerce.seo_service import SeoService

class CategoryNode(TypedDict, total=False):
    id: str
    name: str
    slug: str
    parent_id: Optional[str]
    description: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    image: Optional[str]
    icon: Optional[str]
    created_at: datetime
    product_count: int
    children: List["CategoryNode"]
    category_metadata: Dict[str, object]

logger = logging.getLogger("api-gateway")

class CategoryService:
    @staticmethod
    async def list_categories(db_session: AsyncSession, limit: int = 100, offset: int = 0) -> CategoryListResponse:
        """Moves complex nested listing logic from CategoryController.list_categories. R1.5: Zero-Hydration."""
        # Elite V2.2: Add caching for category tree
        cache_key = "system:categories:tree"
        cached = await xohi_memory.client.get(cache_key)
        if cached:
            return CategoryListResponse(data=[CategoryResponse(**c) for c in json.loads(cached)], total=len(json.loads(cached)))

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
            Category.image, Category.icon, Category.created_at,
            Category.position, Category.show_on_mobile, Category.show_on_desktop,
            Category.category_metadata
        ).where(
            Category.parent_id == None,
            Category.deleted_at == None
        ).order_by(Category.position.asc(), Category.created_at.asc()).limit(limit).offset(offset)

        res = await db_session.execute(stmt)
        parent_rows = res.all()

        if not parent_rows:
            return CategoryListResponse(data=[], total=total)

        parent_ids = [str(r.id) for r in parent_rows]

        # Fetch children (Zero-Hydration)
        child_stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.icon, Category.created_at,
            Category.position, Category.show_on_mobile, Category.show_on_desktop,
            Category.category_metadata
        ).where(
            Category.parent_id.in_(parent_ids),
            Category.deleted_at == None
        ).order_by(Category.position.asc(), Category.created_at.asc())

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
            c_res = await db_session.execute(query, {"ids": all_cat_ids})
            count_map = {str(r.category_id): r.cnt for r in c_res.all()}

        # 3. Tree Reconstruction
        children_by_parent = defaultdict(list)
        for r in child_rows:
            children_by_parent[str(r.parent_id)].append({
                "id": str(r.id),
                "name": r.name,
                "slug": r.slug,
                "parentId": str(r.parent_id),
                "description": r.description,
                "seoTitle": r.seo_title,
                "seoDescription": r.seo_description,
                "image": r.image,
                "icon": r.icon,
                "position": r.position,
                "showOnMobile": r.show_on_mobile,
                "showOnDesktop": r.show_on_desktop,
                "category_metadata": r.category_metadata,
                "productCount": count_map.get(str(r.id), 0),
                "children": [],
                "createdAt": r.created_at.isoformat() if r.created_at else None
            })

        data = []
        for r in parent_rows:
            data.append(CategoryResponse(
                id=str(r.id),
                name=r.name,
                slug=r.slug,
                parent_id=str(r.parent_id) if r.parent_id else None,
                description=r.description,
                seo_title=r.seo_title,
                seo_description=r.seo_description,
                image=r.image,
                icon=r.icon,
                position=r.position,
                show_on_mobile=r.show_on_mobile,
                show_on_desktop=r.show_on_desktop,
                category_metadata=r.category_metadata,
                product_count=count_map.get(str(r.id), 0),
                children=children_by_parent[str(r.id)],
                created_at=r.created_at or datetime.now(timezone.utc)
            ))

        # Cache tree for 1 hour
        await xohi_memory.client.set("system:categories:tree", json.dumps([d.model_dump(mode='json') for d in data]), ex=3600)
        return CategoryListResponse(data=data, total=total)

    @staticmethod
    async def get_category_by_slug(db_session: AsyncSession, slug: str) -> Optional[CategoryResponse]:
        """Fetch category detail by slug with SEO metadata."""
        stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.icon, Category.created_at,
            Category.position, Category.show_on_mobile, Category.show_on_desktop,
            Category.category_metadata
        ).where(
            Category.slug == slug,
            Category.deleted_at == None
        )
        res = await db_session.execute(stmt)
        row = res.first()
        if not row:
            return None
            
        p_dict: dict = dict(row._mapping)
        # Count products for this specific category
        query = text(
            'SELECT COUNT(*)::int as cnt FROM product_bases '
            'WHERE category_id = :cid AND deleted_at IS NULL'
        )
        count_res = await db_session.execute(query, {"cid": str(row.id)})
        p_dict["product_count"] = count_res.scalar() or 0
        p_dict["children"] = []
        
        # SEO Meta Generation
        faqs = p_dict.get("category_metadata", {}).get("faqs", [])
        seo_meta = SeoService.generate_category_seo_meta(
            name=p_dict["name"],
            slug=p_dict["slug"],
            description=p_dict.get("seo_description") or p_dict.get("description"),
            faqs=faqs
        )
        p_dict["seo_meta"] = seo_meta

        return CategoryResponse.model_validate(p_dict)

    @staticmethod
    async def _invalidate_cache() -> None:
        """Invalidate category cache."""
        await xohi_memory.client.delete("system:categories:tree")

    @staticmethod
    async def create_category(db_session: AsyncSession, data: CreateCategoryRequest) -> SuccessResponse:
        new_id = str(uuid.uuid4())
        category = Category(
            id=new_id,
            name=data.name,
            slug=data.slug or str(uuid.uuid4())[:8],
            parent_id=data.parentId,
            description=data.description,
            seo_title=data.seoTitle,
            seo_description=data.seoDescription,
            image=data.image,
            icon=data.icon,
            position=data.position,
            show_on_mobile=data.showOnMobile,
            show_on_desktop=data.showOnDesktop,
            category_metadata=data.metadata.model_dump()
        )
        db_session.add(category)
        await db_session.commit()
        await CategoryService._invalidate_cache()
        await CategoryService._sync_media_links(new_id, data.image)

        cat_data = CategoryResponse(
            id=new_id,
            name=category.name,
            slug=category.slug,
            parent_id=category.parent_id,
            product_count=0,
            children=[],
            description=category.description,
            seo_title=category.seo_title,
            seo_description=category.seo_description,
            image=category.image,
            icon=category.icon,
            position=category.position,
            show_on_mobile=category.show_on_mobile,
            show_on_desktop=category.show_on_desktop,
            category_metadata=category.category_metadata,
            created_at=datetime.now(timezone.utc)
        )
        return SuccessResponse(ok=True, id=new_id, data=cat_data)

    @staticmethod
    async def update_category(db_session: AsyncSession, category_id: str, data: UpdateCategoryRequest) -> SuccessResponse:
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
        if data.icon is not None: category.icon = data.icon
        if data.position is not None: category.position = data.position
        if data.showOnMobile is not None: category.show_on_mobile = data.showOnMobile
        if data.showOnDesktop is not None: category.show_on_desktop = data.showOnDesktop
        if data.metadata is not None: category.category_metadata = data.metadata.model_dump()

        category.updated_at = datetime.now(timezone.utc)
        await db_session.commit()
        await CategoryService._invalidate_cache()
        await CategoryService._sync_media_links(category_id, category.image)

        # Elite V2.2: Deep Sync SEO Meta after update
        faqs = category.category_metadata.get("faqs", []) if category.category_metadata else []
        seo_meta = SeoService.generate_category_seo_meta(
            name=category.name,
            slug=category.slug,
            description=category.seo_description or category.description,
            faqs=faqs
        )

        # 1. Zero-Hydration Response Reconstruction
        # Elite V2.2: Ensure metadata is properly typed before response
        from backend.schemas.category import CategoryMetadata
        verified_metadata = CategoryMetadata.model_validate(category.category_metadata) if category.category_metadata else CategoryMetadata()

        cat_data = CategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            parent_id=str(category.parent_id) if category.parent_id else None,
            product_count=0, # Will be refreshed on total list fetch
            children=[],
            description=category.description,
            seo_title=category.seo_title,
            seo_description=category.seo_description,
            image=category.image,
            icon=category.icon,
            position=category.position,
            show_on_mobile=category.show_on_mobile,
            show_on_desktop=category.show_on_desktop,
            category_metadata=verified_metadata, # Pydantic will handle the alias to 'metadata' if defined
            created_at=category.created_at or datetime.now(timezone.utc),
            seo_meta=seo_meta
        )
        return SuccessResponse(ok=True, id=category_id, data=cat_data)

    @staticmethod
    async def delete_category(db_session: AsyncSession, category_id: str) -> SuccessResponse:
        stmt = select(Category).where(Category.id == category_id)
        res = await db_session.execute(stmt)
        category = res.scalar_one_or_none()
        if not category:
            raise NotFoundException(f"Category {category_id} not found")
        category.deleted_at = datetime.now(timezone.utc)
        return SuccessResponse(ok=True, id=category_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(Category).where(Category.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def reorder_categories(db_session: AsyncSession, ids: List[str]) -> SuccessResponse:
        for index, cat_id in enumerate(ids):
            stmt = update(Category).where(Category.id == cat_id).values(position=index)
            await db_session.execute(stmt)
        await db_session.commit()
        await CategoryService._invalidate_cache()
        return SuccessResponse(ok=True)

    @staticmethod
    async def bulk_update_status(db_session: AsyncSession, ids: List[str], active: bool) -> BulkActionResponse:
        stmt = update(Category).where(Category.id.in_(ids)).values(
            show_on_mobile=active,
            show_on_desktop=active,
            updated_at=datetime.now(timezone.utc)
        )
        await db_session.execute(stmt)
        await CategoryService._invalidate_cache()
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def _sync_media_links(category_id: str, image_url: Optional[str]) -> None:
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

async def provide_category_service() -> CategoryService:
    return category_service
