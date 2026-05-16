import logging
from typing import List, Dict
import sqlalchemy as sa
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import ProductBase
from backend.schemas.product import UpdateProductRequest
from backend.schemas.common import BulkActionResponse

logger = logging.getLogger("api-gateway")

async def bulk_delete_logic(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
    """Elite V2.2: Atomic Bulk Delete."""
    stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(deleted_at=sa.func.now())
    await db_session.execute(stmt)
    return BulkActionResponse(ok=True, count=len(ids))

async def bulk_activate_logic(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
    """Elite V2.2: Atomic Bulk Activate."""
    stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(status="ACTIVE")
    await db_session.execute(stmt)
    return BulkActionResponse(ok=True, count=len(ids))

async def bulk_update_logic(db_session: AsyncSession, ids: List[str], data: UpdateProductRequest) -> BulkActionResponse:
    """Elite V2.2: Optimized Bulk Update with dynamic mapping."""
    update_data = data.model_dump(exclude_unset=True, by_alias=False)
    
    # Mapping table: frontend_field -> database_column
    field_mapping = {
        "name": "name",
        "sku": "sku",
        "price": "price",
        "discountPrice": "discount_price",
        "stock": "stock",
        "status": lambda v: v.upper(),
        "isAiFeatured": "is_ai_featured",
        "categoryId": "category_id",
        "shortDescription": "short_description",
        "description": "description",
        "slug": "slug",
        "seoTitle": "seo_title",
        "seoDescription": "seo_description",
        "seoKeywords": "seo_keywords",
        "images": "images",
        "mobileImages": "mobile_images",
        "attributes": "attributes",
        "metadata": "product_metadata",
        "tierVariations": "tier_variations"
    }

    db_data = {}
    for key, value in update_data.items():
        if key in field_mapping:
            target = field_mapping[key]
            if callable(target):
                db_data[key.replace("Price", "_price").replace("Id", "_id")] = target(value) # Basic snake_case guess or manual override
            else:
                db_data[target] = value

    if not db_data:
        return BulkActionResponse(ok=True, count=0)

    stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(**db_data)
    await db_session.execute(stmt)
    return BulkActionResponse(ok=True, count=len(ids))
