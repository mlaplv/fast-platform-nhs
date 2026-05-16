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

async def list_products_logic(
    db_session: AsyncSession,
    category_slug: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status: Optional[str] = None,
    is_ai_featured: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> ProductListResponse:
    """Elite V2.2: Advanced Product Query & Filtering (Isolated)."""
    stmt = select(ProductBase).where(ProductBase.deleted_at == None)

    # 1. Filter by Category
    if category_slug:
        cat_stmt = select(Category.id).where(Category.slug == category_slug)
        cat_id = (await db_session.execute(cat_stmt)).scalar_one_or_none()
        if cat_id:
            stmt = stmt.where(ProductBase.category_id == cat_id)

    # 2. Advanced Search (Elite Noise Cleaning)
    if search:
        clean_search = noise_cleaner(search)
        search_pattern = f"%{escape_like(clean_search)}%"
        stmt = stmt.where(
            or_(
                ProductBase.name.ilike(search_pattern),
                ProductBase.sku.ilike(search_pattern),
                ProductBase.short_description.ilike(search_pattern)
            )
        )

    # 3. Price Range
    if min_price is not None:
        stmt = stmt.where(ProductBase.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(ProductBase.price <= max_price)

    # 4. Status & AI Featured
    if status:
        stmt = stmt.where(ProductBase.status == status.upper())
    if is_ai_featured is not None:
        stmt = stmt.where(ProductBase.is_ai_featured == is_ai_featured)

    # 5. Total Count (Parallel-ready)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db_session.execute(count_stmt)).scalar_one()

    # 6. Sorting
    sort_col = getattr(ProductBase, sort_by, ProductBase.created_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_col.desc())
    else:
        stmt = stmt.order_by(sort_col.asc())

    # 7. Pagination
    stmt = stmt.limit(limit).offset(offset)
    result = await db_session.execute(stmt)
    products = result.scalars().all()

    return ProductListResponse(
        data=[ProductResponse.model_validate(p) for p in products],
        total=total,
        limit=limit,
        offset=offset
    )

async def get_product_logic(db_session: AsyncSession, product_id: str) -> ProductResponse:
    """Elite V2.2: Single Product Fetch (Isolated)."""
    stmt = select(ProductBase).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
    product = (await db_session.execute(stmt)).scalar_one_or_none()
    if not product:
        raise NotFoundException(f"Product {product_id} not found")
    return ProductResponse.model_validate(product)

async def get_product_by_slug_logic(db_session: AsyncSession, slug: str) -> ProductResponse:
    """Elite V2.2: Slug-based Product Fetch (Isolated)."""
    stmt = select(ProductBase).where(ProductBase.slug == slug, ProductBase.deleted_at == None)
    product = (await db_session.execute(stmt)).scalar_one_or_none()
    if not product:
        raise NotFoundException(f"Product with slug '{slug}' not found")
    return ProductResponse.model_validate(product)
