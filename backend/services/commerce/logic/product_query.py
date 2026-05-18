import logging
import sqlalchemy as sa
from sqlalchemy import select, func, and_, or_
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException
from backend.database.models import ProductBase, Category, ProductVariant
from backend.schemas.product import ProductResponse, ProductListResponse, SearchFacets
from backend.utils.sql import escape_like
from backend.utils.noise_cleaner import noise_cleaner

logger = logging.getLogger("api-gateway")

def _get_base_query():
    """Elite V2.2: Centralized projection to prevent MissingGreenlet errors."""
    return select(
        ProductBase.id, ProductBase.name, ProductBase.sku,
        ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
        ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
        ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
        ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
        ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
        ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
        Category.name.label("category_name"), Category.slug.label("category_slug")
    ).outerjoin(Category, ProductBase.category_id == Category.id)

async def list_products_logic(
    db_session: AsyncSession,
    category_slug: Optional[str] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status: Optional[str] = None,
    featured_only: bool = False,
    brand: Optional[str] = None,
    origin: Optional[str] = None,
    product_ids: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> ProductListResponse:
    """Elite V2.2: Advanced Product Query & Filtering (Isolated & Hardened)."""
    stmt = _get_base_query().where(ProductBase.deleted_at == None)

    # 1. Filters
    if category_slug:
        stmt = stmt.where(Category.slug == category_slug)
    if category_id:
        stmt = stmt.where(ProductBase.category_id == category_id)
    if product_ids:
        stmt = stmt.where(ProductBase.id.in_(product_ids))
    if featured_only:
        stmt = stmt.where(ProductBase.is_ai_featured == True)
    
    if search:
        # Elite Noise Cleaning for Search Query
        clean_search = await noise_cleaner.clean(search)
        search_pattern = f"%{escape_like(clean_search)}%"
        stmt = stmt.where(
            or_(
                ProductBase.name.ilike(search_pattern),
                ProductBase.sku.ilike(search_pattern)
            )
        )

    if brand:
        stmt = stmt.where(ProductBase.attributes["brand"].astext == brand)
    if origin:
        stmt = stmt.where(ProductBase.attributes["origin"].astext == origin)

    if min_price is not None:
        stmt = stmt.where(ProductBase.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(ProductBase.price <= max_price)
    if status:
        stmt = stmt.where(ProductBase.status == status.upper())

    # 2. Total Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db_session.execute(count_stmt)).scalar_one()

    # 3. Sorting & Pagination
    sort_col = getattr(ProductBase, sort_by, ProductBase.created_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_col.desc())
    else:
        stmt = stmt.order_by(sort_col.asc())

    stmt = stmt.limit(limit).offset(offset)
    result = await db_session.execute(stmt)
    # R2026: Use mappings to prevent MissingGreenlet errors during Pydantic validation
    rows = result.mappings().all()

    # Elite V2.2: Fast bulk fetch for review counts
    review_counts = {}
    if rows:
        from backend.database.models import SystemReview
        rc_stmt = select(SystemReview.entity_id, func.count(SystemReview.id)).where(
            SystemReview.entity_id.in_([r["id"] for r in rows]),
            SystemReview.entity_type == "PRODUCT",
            SystemReview.status == "APPROVED"
        ).group_by(SystemReview.entity_id)
        rc_res = await db_session.execute(rc_stmt)
        review_counts = {r[0]: r[1] for r in rc_res.all()}

    data = []
    for row in rows:
        row_dict = dict(row)
        row_dict["review_count"] = review_counts.get(row_dict["id"], 0)
        # Fetch variants separately to avoid complex joins
        v_stmt = select(ProductVariant).where(
            ProductVariant.product_base_id == row_dict["id"],
            ProductVariant.deleted_at == None
        )
        variants = (await db_session.execute(v_stmt)).scalars().all()
        row_dict["variants"] = list(variants)
        data.append(ProductResponse.model_validate(row_dict))

    return ProductListResponse(
        data=data,
        total=total,
        limit=limit,
        offset=offset
    )

async def get_product_logic(db_session: AsyncSession, product_id: str) -> ProductResponse:
    """Elite V2.2: Single Product Fetch (Hardened)."""
    stmt = _get_base_query().where(ProductBase.id == product_id, ProductBase.deleted_at == None)
    result = await db_session.execute(stmt)
    row = result.mappings().first()
    if not row:
        raise NotFoundException(f"Product {product_id} not found")
    
    row_dict = dict(row)
    v_stmt = select(ProductVariant).where(
        ProductVariant.product_base_id == product_id,
        ProductVariant.deleted_at == None
    )
    variants = (await db_session.execute(v_stmt)).scalars().all()
    row_dict["variants"] = list(variants)
    
    return ProductResponse.model_validate(row_dict)

async def get_product_by_slug_logic(db_session: AsyncSession, slug: str) -> ProductResponse:
    """Elite V2.2: Slug-based Product Fetch (Hardened)."""
    # Normalize slug: remove trailing slashes
    clean_slug = slug.rstrip('/')
    stmt = _get_base_query().where(ProductBase.slug == clean_slug, ProductBase.deleted_at == None)
    result = await db_session.execute(stmt)
    row = result.mappings().first()
    
    if not row:
        # Fallback: exact match with case sensitivity if ilike fails in some DBs
        stmt = _get_base_query().where(ProductBase.slug == slug, ProductBase.deleted_at == None)
        result = await db_session.execute(stmt)
        row = result.mappings().first()

    if not row:
        raise NotFoundException(f"Product with slug '{slug}' not found")
        
    row_dict = dict(row)
    v_stmt = select(ProductVariant).where(
        ProductVariant.product_base_id == row_dict["id"],
        ProductVariant.deleted_at == None
    )
    variants = (await db_session.execute(v_stmt)).scalars().all()
    row_dict["variants"] = list(variants)
    
    return ProductResponse.model_validate(row_dict)
