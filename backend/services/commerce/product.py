import uuid
import logging
from datetime import datetime, timezone
import sqlalchemy as sa
from typing import List, Dict, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import ProductBase, Category, ProductVariant, Order
from backend.schemas.product import CreateProductRequest, UpdateProductRequest, ProductResponse, ProductListResponse
from backend.schemas.common import SuccessResponse, BulkActionResponse
from backend.services.commerce.product_vector import ProductVectorService
from backend.utils.sql import escape_like
from backend.utils.noise_cleaner import noise_cleaner
from sqlalchemy.dialects.postgresql import JSONB
import re

logger = logging.getLogger("api-gateway")
RE_ORDER_COUNT = re.compile(r"([\d,.]+)")

class ProductRowDict(TypedDict):
    """Elite Structural Definition for Product Project Result."""
    id: str
    name: str
    sku: str
    price: float
    discount_price: Optional[float]
    stock: int
    status: str
    category_id: Optional[str]
    category_name: Optional[str]
    short_description: Optional[str]
    description: Optional[str]
    type: str
    slug: str
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: Optional[str]
    images: List[str]
    mobile_images: List[str]
    attributes: Dict[str, object]
    tier_variations: List[Dict[str, object]]
    metadata: Dict[str, object]
    created_at: datetime
    order_count: Optional[int]
    order_count_text: Optional[str]
    variants: Optional[List[object]]

class ProductService:
    """Business Logic for Products (Elite V2.2)."""

    def __init__(self, vector_service: ProductVectorService):
        self.vector_service = vector_service

    async def _get_real_order_count(self, db_session: AsyncSession, product_id: str) -> int:
        """Count actual orders containing this product (Elite V2.2 JSONB Query)."""
        stmt = select(func.count(Order.id)).where(
            Order.items.cast(JSONB).contains([{"id": product_id}]),
            Order.deleted_at == None
        )
        return await db_session.scalar(stmt) or 0

    async def _inject_dynamic_counting(self, db_session: AsyncSession, product_id: str, row_dict: ProductRowDict) -> None:
        """Inject elite dynamic order counting into the product response dictionary."""
        actual_orders = await self._get_real_order_count(db_session, product_id)
        row_dict["order_count"] = actual_orders
        row_dict["order_count_text"] = self._get_display_order_count_text(row_dict.get("metadata", {}), actual_orders)

    def _get_display_order_count_text(self, metadata: Dict[str, object], actual_count: int) -> str:
        """Combine real orders with social proof base from metadata (Vietnamese Format)."""
        base_text = str(metadata.get("reviews_count_text", "2.140+ LƯỢT MUA"))
        match = RE_ORDER_COUNT.search(base_text)
        
        base_num = 0
        if match:
            # Normalize: strip all thousands separators before parsing
            clean_num = match.group(1).replace(",", "").replace(".", "")
            base_num = int(clean_num) if clean_num.isdigit() else 0
        
        display_total = base_num + actual_count
        # format with comma, then swap to dots for VN standard
        return f"{display_total:,}+ LƯỢT MUA".replace(",", ".")

    async def list_products(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ProductListResponse:
        """List products (R76: Scalar Projection). R1.5: Zero-Hydration."""
        conditions = [ProductBase.deleted_at == None]
        if status and status != "all":
            conditions.append(ProductBase.status == status.upper())
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                func.unaccent(ProductBase.name).ilike(f"%{func.unaccent(safe)}%"),
                ProductBase.sku.ilike(f"%{safe}%"),
            ))

        # 1. COUNT (Zero-Hydration)
        count_stmt = select(func.count(ProductBase.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # 2. R76: Scalar Projection Fetch
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, ProductBase.product_metadata.label("metadata"),
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(ProductBase.created_at.desc())

        result = await db_session.execute(stmt)
        data: List[ProductResponse] = []
        for row in result:
            row_dict: ProductRowDict = dict(row._mapping)  # type: ignore
            row_dict["variants"] = [] # Optimize: don't load variants in list view
            data.append(ProductResponse.model_validate(row_dict))
            
        return ProductListResponse(data=data, total=total)

    async def get_product(self, db_session: AsyncSession, product_id: str) -> ProductResponse:
        """Get a single product (R76: Scalar Projection)."""
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, ProductBase.product_metadata.label("metadata"),
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            ProductBase.id == product_id,
            ProductBase.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Product {product_id} not found")

        # Fetch variants
        v_stmt = select(ProductVariant).where(ProductVariant.product_base_id == product_id, ProductVariant.deleted_at == None)
        variants = (await db_session.execute(v_stmt)).scalars().all()
        
        row_dict: ProductRowDict = dict(row._mapping) # type: ignore
        row_dict["variants"] = list(variants)
        
        # Elite Dynamic Counting
        await self._inject_dynamic_counting(db_session, product_id, row_dict)

        return ProductResponse.model_validate(row_dict)

    async def get_product_by_slug(self, db_session: AsyncSession, slug: str) -> ProductResponse:
        """Get a single product by slug (R76: Scalar Projection)."""
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, ProductBase.product_metadata.label("metadata"),
            ProductBase.created_at,
            Category.name.label("category_name")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            ProductBase.slug == slug,
            ProductBase.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Product with slug '{slug}' not found")

        product_id = row.id
        # Fetch variants
        v_stmt = select(ProductVariant).where(ProductVariant.product_base_id == product_id, ProductVariant.deleted_at == None)
        variants = (await db_session.execute(v_stmt)).scalars().all()
        
        row_dict: ProductRowDict = dict(row._mapping) # type: ignore
        row_dict["variants"] = list(variants)
        
        # Elite Dynamic Counting
        await self._inject_dynamic_counting(db_session, product_id, row_dict)

        return ProductResponse.model_validate(row_dict)

    async def create_product(self, db_session: AsyncSession, data: CreateProductRequest) -> SuccessResponse:
        """Create a new product and its embedding."""
        new_id = str(uuid.uuid4())

        # Phase 76.95: Advanced Structural Noise Cleaning (Elite V2.2)
        cleaned_description = await noise_cleaner.clean(data.description, strip_html=False) if data.description else ""

        product = ProductBase(
            id=new_id,
            name=data.name,
            sku=data.sku,
            price=data.price,
            discount_price=data.discountPrice,
            stock=data.stock,
            status=data.status.upper(),
            short_description=data.shortDescription,
            description=cleaned_description,
            category_id=data.categoryId,
            type=data.type,
            slug=data.slug,
            seo_title=data.seoTitle,
            seo_description=data.seoDescription,
            seo_keywords=data.seoKeywords,
            images=data.images,
            mobile_images=data.mobileImages,
            attributes=data.attributes,
            tier_variations=[tv.model_dump() for tv in data.tierVariations] if data.tierVariations else [],
            product_metadata=data.metadata.model_dump() if data.metadata else {},
        )
        db_session.add(product)

        # Add variants
        if data.variants:
            for v in data.variants:
                v_id = v.id if v.id and len(v.id) > 5 else f"v_{uuid.uuid4().hex[:12]}"
                variant = ProductVariant(
                    id=v_id,
                    product_base_id=new_id,
                    tier_index=v.tierIndex,
                    sku=v.sku if v.sku and v.sku.strip() else None,
                    price=v.price,
                    discount_price=v.discountPrice,
                    stock=v.stock
                )
                db_session.add(variant)

        await db_session.commit() # Ensure product exists for RAG foreign key
        await db_session.refresh(product)

        # RAG Upsert
        await self.vector_service.upsert_product_embedding(
            db_session, new_id, data.name, cleaned_description
        )

        return SuccessResponse(ok=True, id=new_id)

    async def update_product(self, db_session: AsyncSession, product_id: str, data: UpdateProductRequest) -> SuccessResponse:
        """Update a product and its embedding."""
        # Rule 1.5: Detail fetch for update (Surgical)
        stmt = select(ProductBase).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
        result = await db_session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise NotFoundException(f"Product {product_id} not found")

        if data.name is not None: product.name = data.name
        if data.sku is not None: product.sku = data.sku
        if data.price is not None: product.price = data.price
        if data.discountPrice is not None: product.discount_price = data.discountPrice
        if data.stock is not None: product.stock = data.stock
        if data.status is not None: product.status = data.status.upper()
        if data.shortDescription is not None: product.short_description = data.shortDescription

        if data.description is not None:
            # Phase 76.95: Advanced Structural Noise Cleaning (Elite V2.2)
            product.description = await noise_cleaner.clean(data.description, strip_html=False)

        if data.categoryId is not None: product.category_id = data.categoryId
        if data.slug is not None: product.slug = data.slug
        if data.seoTitle is not None: product.seo_title = data.seoTitle
        if data.seoDescription is not None: product.seo_description = data.seoDescription
        if data.seoKeywords is not None: product.seo_keywords = data.seoKeywords
        if data.images is not None: product.images = data.images
        if data.mobileImages is not None: product.mobile_images = data.mobileImages
        if data.attributes is not None: product.attributes = data.attributes
        if data.tierVariations is not None: product.tier_variations = [tv.model_dump() for tv in data.tierVariations]
        if data.metadata is not None: product.product_metadata = data.metadata.model_dump()

        if data.variants is not None:
            # Delete old variants strictly (Hard delete to avoid PK conflicts if reusing IDs)
            await db_session.execute(delete(ProductVariant).where(ProductVariant.product_base_id == product_id))
            # Insert new ones
            for v in data.variants:
                v_id = v.id if v.id and not v.id.startswith('new_') else f"v_{uuid.uuid4().hex[:12]}"
                variant = ProductVariant(
                    id=v_id,
                    product_base_id=product_id,
                    tier_index=v.tierIndex,
                    sku=v.sku if v.sku and v.sku.strip() else None,
                    price=v.price,
                    discount_price=v.discountPrice,
                    stock=v.stock
                )
                db_session.add(variant)

        if data.name is not None or data.description is not None:
            await self.vector_service.upsert_product_embedding(
                db_session, product_id, product.name, product.description
            )

        return SuccessResponse(ok=True, id=product_id)

    async def delete_product(self, db_session: AsyncSession, product_id: str) -> SuccessResponse:
        stmt = update(ProductBase).where(ProductBase.id == product_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=product_id)

    async def bulk_delete(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_activate(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(status="ACTIVE")
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_product_service(vector_service: ProductVectorService) -> ProductService:
    """Standard Litestar Provider for ProductService."""
    return ProductService(vector_service=vector_service)
