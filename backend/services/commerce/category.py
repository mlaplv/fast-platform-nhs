import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, TypedDict
from pydantic import JsonValue
from collections import defaultdict

from sqlalchemy import text, select, func, update, delete as sql_delete
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

        # 1. Optimized Fetch ALL (Rule 1.5 - Scalar Projection / Zero-Hydration)
        # Elite V2.2: We fetch ALL categories in one go for N-Level Tree Building
        stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.icon, Category.created_at,
            Category.position, Category.show_on_mobile, Category.show_on_desktop,
            Category.category_metadata
        ).where(
            Category.deleted_at == None
        ).order_by(Category.position.asc(), Category.created_at.asc())

        res = await db_session.execute(stmt)
        all_rows = res.all()

        if not all_rows:
            return CategoryListResponse(data=[], total=0)

        all_cat_ids = [str(r.id) for r in all_rows]

        # N+1 KILL: Single raw SQL to get ALL product counts grouped by categoryId
        count_map: Dict[str, int] = {}
        if all_cat_ids:
            query = text(
                'SELECT category_id, COUNT(*)::int as cnt FROM product_bases '
                'WHERE category_id = ANY(:ids) AND deleted_at IS NULL '
                'GROUP BY category_id'
            )
            c_res = await db_session.execute(query, {"ids": all_cat_ids})
            count_map = {str(r.category_id): r.cnt for r in c_res.all()}

        # 3. N-Level Tree Reconstruction in O(N)
        cat_map: Dict[str, CategoryResponse] = {}
        for r in all_rows:
            # Pydantic alias will handle correct serialization
            cat_map[str(r.id)] = CategoryResponse(
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
                children=[],
                created_at=r.created_at or datetime.now(timezone.utc)
            )

        data = []
        # Re-iterate to build the hierarchy
        for r in all_rows:
            cat_obj = cat_map[str(r.id)]
            if r.parent_id and str(r.parent_id) in cat_map:
                cat_map[str(r.parent_id)].children.append(cat_obj)
            elif not r.parent_id:
                data.append(cat_obj)
        
        total = len(data)
        paginated_data = data[offset:offset+limit] if limit else data

        # Cache tree for 1 hour
        await xohi_memory.client.set("system:categories:tree", json.dumps([d.model_dump(mode='json') for d in data]), ex=3600)
        return CategoryListResponse(data=data, total=total)

    @staticmethod
    async def get_category_by_slug(db_session: AsyncSession, slug: str) -> Optional[CategoryResponse]:
        """Fetch category detail by slug with SEO metadata."""
        from backend.database import current_tenant_id
        tid = current_tenant_id.get()
        
        stmt = select(
            Category.id, Category.name, Category.slug, Category.parent_id,
            Category.description, Category.seo_title, Category.seo_description,
            Category.image, Category.icon, Category.created_at,
            Category.position, Category.show_on_mobile, Category.show_on_desktop,
            Category.category_metadata
        ).where(
            Category.slug == slug,
            Category.deleted_at == None,
            Category.tenant_id == tid
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
            description=p_dict.get("description"),
            faqs=faqs,
            seo_title=p_dict.get("seo_title"),
            seo_description=p_dict.get("seo_description")
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
            description=category.description,
            faqs=faqs,
            seo_title=category.seo_title,
            seo_description=category.seo_description
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
    async def _check_deletable(db_session: AsyncSession, ids: List[str], include_soft_deleted_children: bool = False) -> tuple[List[str], List[str]]:
        """Elite V2.2: Batch-check xem ID nào có sản phẩm hoặc có danh mục con → không được xóa.
        Returns: (deletable_ids, blocked_ids)
        """
        if not ids:
            return [], []

        # 1. Check categories có con
        if include_soft_deleted_children:
            child_stmt = select(Category.parent_id).where(
                Category.parent_id.in_(ids)
            ).distinct()
        else:
            child_stmt = select(Category.parent_id).where(
                Category.parent_id.in_(ids),
                Category.deleted_at == None  # noqa
            ).distinct()
        child_res = await db_session.execute(child_stmt)
        has_children_ids: set[str] = {str(r.parent_id) for r in child_res.all()}

        # 2. Check categories có sản phẩm chưa xóa
        prod_stmt = text(
            "SELECT DISTINCT category_id FROM product_bases "
            "WHERE category_id = ANY(:ids) AND deleted_at IS NULL"
        )
        prod_res = await db_session.execute(prod_stmt, {"ids": ids})
        has_products_ids: set[str] = {str(r.category_id) for r in prod_res.all()}

        blocked: set[str] = has_children_ids | has_products_ids
        deletable = [i for i in ids if i not in blocked]
        return deletable, list(blocked)

    @staticmethod
    async def delete_category(db_session: AsyncSession, category_id: str) -> SuccessResponse:
        """R18: Soft delete — Guard: Từ chối nếu có sản phẩm hoặc danh mục con."""
        deletable, blocked = await CategoryService._check_deletable(db_session, [category_id])
        if blocked:
            from litestar.exceptions import ValidationException
            raise ValidationException(
                detail=f"BLOCKED: Danh mục này có sản phẩm hoặc danh mục con. Hãy di chuyển hoặc xóa chúng trước."
            )
        stmt = select(Category).where(Category.id == category_id)
        res = await db_session.execute(stmt)
        category = res.scalar_one_or_none()
        if not category:
            raise NotFoundException(f"Category {category_id} not found")
        category.deleted_at = datetime.now(timezone.utc)
        await CategoryService._invalidate_cache()
        return SuccessResponse(ok=True, id=category_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        """Soft delete hàng loạt — Chỉ xóa được ID không có con và không có sản phẩm."""
        deletable, blocked = await CategoryService._check_deletable(db_session, ids)
        if deletable:
            stmt = update(Category).where(Category.id.in_(deletable)).values(deleted_at=datetime.now(timezone.utc))
            await db_session.execute(stmt)
            await CategoryService._invalidate_cache()
        return BulkActionResponse(ok=True, count=len(deletable), skipped=blocked)

    @staticmethod
    async def hard_delete_category(db_session: AsyncSession, category_id: str) -> SuccessResponse:
        """Xóa vĩnh viễn 1 category — Guard: Không cho phép nếu có sản phẩm hoặc danh mục con (kể cả đã bị soft-deleted)."""
        deletable, blocked = await CategoryService._check_deletable(db_session, [category_id], include_soft_deleted_children=True)
        if blocked:
            from litestar.exceptions import ValidationException
            raise ValidationException(
                detail=f"BLOCKED: Danh mục có sản phẩm hoặc danh mục con (kể cả đã ẩn). Hãy di chuyển hoặc xóa chúng trước."
            )
        stmt = sql_delete(Category).where(Category.id == category_id)
        await db_session.execute(stmt)
        await CategoryService._invalidate_cache()
        logger.warning(f"[CategoryService] HARD DELETE executed for category_id={category_id}")
        return SuccessResponse(ok=True, id=category_id)

    @staticmethod
    async def bulk_hard_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        """Xóa vĩnh viễn hàng loạt — Chỉ purge ID không có con (kể cả đã ẩn) và không có sản phẩm."""
        deletable, blocked = await CategoryService._check_deletable(db_session, ids, include_soft_deleted_children=True)
        if deletable:
            stmt = sql_delete(Category).where(Category.id.in_(deletable))
            await db_session.execute(stmt)
            await CategoryService._invalidate_cache()
            logger.warning(f"[CategoryService] BULK HARD DELETE executed for ids={deletable}")
        return BulkActionResponse(ok=True, count=len(deletable), skipped=blocked)


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
