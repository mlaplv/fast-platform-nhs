import uuid
import logging
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import select, func, and_, or_, update, delete
from typing import List, Dict, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database import current_tenant_id
from backend.database.models import ProductBase, Category, ProductVariant, Order
from backend.schemas.product import CreateProductRequest, UpdateProductRequest, ProductResponse, ProductListResponse, SearchFacets
from backend.schemas.common import SuccessResponse, BulkActionResponse
from backend.services.commerce.product_vector import ProductVectorService
from backend.utils.sql import escape_like
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.event_bus import event_bus
from backend.utils.media import extract_media_urls
from backend.services.commerce.logic.product_ai import suggest_seo_logic, suggest_faqs_logic, suggest_ingredients_logic, suggest_specs_logic, suggest_semantic_logic, suggest_ingredients_grouped_logic
from backend.services.commerce.logic.viral_hydration import hydrate_viral_config_logic, sanitize_vouchers_logic
from backend.services.commerce.logic.product_bulk import bulk_delete_logic, bulk_activate_logic, bulk_update_logic
from backend.services.commerce.logic.product_query import list_products_logic, get_product_logic, get_product_by_slug_logic
from sqlalchemy.dialects.postgresql import JSONB

import re
import json
import hashlib
import math
import os

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
    is_ai_featured: bool
    variants: Optional[List[object]]

class ProductService:
    """Business Logic for Products (Elite V2.2)."""

    def __init__(self, vector_service: ProductVectorService):
        self.vector_service = vector_service
        # Đăng ký listener để tự động cập nhật order_count khi có đơn hàng mới
        event_bus.subscribe("ORDER_CREATED", self._handle_order_created)

    async def _handle_order_created(self, payload: Dict[str, object]) -> None:
        """
        Elite V2.2: Async Listener - Denormalization Sync.
        Tự động tăng order_count cho các sản phẩm trong đơn hàng.
        """
        items = payload.get("items", [])
        if not isinstance(items, list):
            return

        from backend.database.read_session import read_session_maker
        # Sử dụng read_session_maker hoặc tạo session mới để update
        # Vì listener chạy background, ta cần tự quản lý session
        async with read_session_maker() as db_session:
            try:
                for item in items:
                    if isinstance(item, dict) and "id" in item:
                        pid = str(item["id"])
                        stmt = update(ProductBase).where(ProductBase.id == pid).values(
                            order_count=ProductBase.order_count + 1
                        )
                        await db_session.execute(stmt)
                await db_session.commit()
                logger.info(f"[ProductService] Denormalized order_count updated for {len(items)} items")
            except Exception as e:
                logger.error(f"[ProductService] Denormalization failed: {e}")
                await db_session.rollback()

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

    def _inject_marketing_boost(self, row_dict: ProductRowDict) -> None:
        # Elite V2.2: Marketing Boost (G_BY_COUNT) + Deterministic FOMO Growth
        try:
            g_by_count = int(os.getenv("G_BY_COUNT", "0"))
        except (ValueError, TypeError):
            g_by_count = 0
            
        # 🎯 Elite FOMO Logic: Hourly Growth + Unique Product Offset
        now = datetime.now(timezone.utc)
        hour_factor = now.hour * 2
        min_factor = now.minute // 15
        
        # Unique deterministic offset per product (500 to 8000 range)
        # Using MD5 instead of hash() to ensure persistence across process restarts
        pid_str = str(row_dict.get("id", ""))
        pid_hash = int(hashlib.md5(pid_str.encode()).hexdigest(), 16)
        unique_offset = (pid_hash % 150) * 50 # Variates by up to 7500
        
        fomo_boost = hour_factor + min_factor + unique_offset
        
        raw_count = int(row_dict.get("order_count") or 0)
        total_boosted_count = raw_count + g_by_count + fomo_boost
        
        row_dict["order_count_text"] = self._get_display_order_count_text(row_dict.get("metadata", {}), raw_count + fomo_boost)
        row_dict["order_count"] = total_boosted_count

    def _get_display_order_count_text(self, metadata: Dict[str, object], actual_count: int) -> str:
        """Combine real orders with social proof base from metadata (Vietnamese Format)."""
        try:
            g_by_count = int(os.getenv("G_BY_COUNT", "0"))
        except (ValueError, TypeError):
            g_by_count = 0

        base_text = str(metadata.get("reviews_count_text", "2,140+ LƯỢT MUA"))
        match = RE_ORDER_COUNT.search(base_text)
        
        base_num = 0
        if match:
            # Normalize: strip all thousands separators before parsing
            clean_num = match.group(1).replace(",", "").replace(".", "")
            base_num = int(clean_num) if clean_num.isdigit() else 0
        
        display_total = base_num + actual_count + g_by_count
        
        if display_total > 0:
            if display_total >= 1000:
                # Elite V2.2: Clean numeric display only, prefix/suffix handled by UI
                return f"{display_total:,}".replace(",", ".")
            else:
                return str(display_total)
        return ""

    async def _hydrate_viral_config(self, db_session: AsyncSession, row_dict: ProductRowDict) -> None:
        """Elite V2.2: Dynamic hydration (Delegated)."""
        await hydrate_viral_config_logic(db_session, row_dict)

    def _sanitize_vouchers(self, row_dict: ProductRowDict) -> None:
        """Elite V2.2: Anti-Leakage Protocol (Delegated)."""
        sanitize_vouchers_logic(row_dict)

    async def list_products(
        self,
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
        """Elite V2.2: Advanced Product Query (Delegated)."""
        # Elite Note: We fetch and then hydrate to maintain consistency
        res = await list_products_logic(
            db_session, category_slug, category_id, search, min_price, max_price, 
            status, featured_only, brand, origin, product_ids, limit, offset, sort_by, sort_order
        )
        
        # Post-processing hydration for list
        for prod in res.data:
            await self._hydrate_product_response(db_session, prod)
            
        return res

    async def _hydrate_product_response(self, db_session: AsyncSession, product: ProductResponse) -> None:
        """Elite V2.2: Centralized hydration for responses (Snake-to-Camel Sync)."""
        # R2026: Export to snake_case for internal logic compatibility
        prod_dict = product.model_dump(by_alias=True)
        
        # 1. Marketing & Social Proof (Modifies prod_dict)
        self._inject_marketing_boost(prod_dict)
        
        # 2. Viral Configuration (Modifies prod_dict)
        await self._hydrate_viral_config(db_session, prod_dict)
        
        # 3. Security (Sanitize - Modifies prod_dict)
        self._sanitize_vouchers(prod_dict)
        
        # 4. Sync back to model (Manual mapping for safety)
        product.metadata = prod_dict.get("metadata", product.metadata)
        product.orderCount = prod_dict.get("order_count", product.orderCount)
        product.orderCountText = prod_dict.get("order_count_text", product.orderCountText)

    async def get_product(self, db_session: AsyncSession, product_id: str) -> ProductResponse:
        """Elite V2.2: Single Product Fetch (Delegated)."""
        product_res = await get_product_logic(db_session, product_id)
        await self._hydrate_product_response(db_session, product_res)
        return product_res

    async def get_product_by_slug(self, db_session: AsyncSession, slug: str) -> ProductResponse:
        """Elite V2.2: Slug-based Product Fetch (Delegated)."""
        product_res = await get_product_by_slug_logic(db_session, slug)
        await self._hydrate_product_response(db_session, product_res)
        return product_res

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
        )

        # R00 Compliance: Viral settings are now managed via Promotions (Vouchers)
        # only SKU-specific metadata like social proof or flash sale should be here
        product.product_metadata = data.metadata.model_dump() if data.metadata else {}
        
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
                    stock=v.stock,
                    is_default=v.is_default,
                    attributes=v.attributes.model_dump() if v.attributes else {}
                )
                db_session.add(variant)

        await db_session.commit() # Ensure product exists for RAG foreign key
        await db_session.refresh(product)

        # RAG Upsert
        await self.vector_service.upsert_product_embedding(
            db_session, new_id, data.name, cleaned_description
        )

        # Elite V2.2: Knowledge Graph Generation (SGE Optimization)
        if getattr(data, "generate_knowledge_graph", False):
            from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
            try:
                kg_data = await generate_knowledge_graph(
                    content=cleaned_description,
                    topic=data.name
                )
                product.product_metadata["knowledge_graph"] = kg_data
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(product, "product_metadata")
            except Exception as e:
                logger.error(f"[ProductService] KG Generation failed for {new_id}: {e}")

        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, new_id, product)

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
            logger.info(f"🧬 [ProductService] Updating description for {product_id}. Input len: {len(data.description)}. Snippet: {data.description[:100]}...")
            cleaned = await noise_cleaner.clean(data.description, strip_html=False)
            logger.info(f"🧬 [ProductService] Cleaned description for {product_id}. Result len: {len(cleaned)}. Snippet: {cleaned[:100]}...")
            product.description = cleaned

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
        if data.isAiFeatured is not None: product.is_ai_featured = data.isAiFeatured

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
                    stock=v.stock,
                    is_default=v.is_default,
                    attributes=v.attributes.model_dump() if v.attributes else {}
                )
                db_session.add(variant)

        if data.name is not None or data.description is not None:
            await self.vector_service.upsert_product_embedding(
                db_session, product_id, product.name, product.description
            )
            
            # Elite V2.2: Re-generate Knowledge Graph on content change
            if getattr(data, "generate_knowledge_graph", False):
                from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
                try:
                    kg_data = await generate_knowledge_graph(
                        content=product.description,
                        topic=product.name
                    )
                    if not product.product_metadata:
                        product.product_metadata = {}
                    product.product_metadata["knowledge_graph"] = kg_data
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(product, "product_metadata")
                except Exception as e:
                    logger.error(f"[ProductService] KG Refresh failed for {product_id}: {e}")

        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, product_id, product)

        await db_session.commit()

        return SuccessResponse(ok=True, id=product_id)

    async def _sync_media_links(self, db_session: AsyncSession, product_id: str, product: ProductBase) -> None:
        """
        Elite V2.2: Neural Media Sync.
        Phát sự kiện để MediaResponder xử lý việc đồng bộ liên kết N-N trong background.
        SỬ DỤNG: Recursive Scan trên toàn bộ dữ liệu thực thể.
        """
        try:
            # Chuyển đổi sang dict để extract_media_urls quét đệ quy
            # Bao gồm cả images, mobile_images, tier_variations và product_metadata
            product_data = {
                "images": product.images,
                "mobile_images": product.mobile_images,
                "tier_variations": product.tier_variations,
                "metadata": product.product_metadata,
                "description": product.description # Tìm ảnh trong Tiptap HTML
            }
            
            urls = extract_media_urls(product_data)
            
            # 3. Phát sự kiện (Decoupled Flow)
            if urls:
                await event_bus.emit("MEDIA_SYNC_REQUIRED", {
                    "entity_id": str(product_id),
                    "entity_type": "product",
                    "urls": list(urls)
                })
                logger.info(f"[ProductService] Emitted MEDIA_SYNC_REQUIRED for product {product_id} with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"[ProductService] Failed to emit media sync: {e}")

    async def delete_product(self, db_session: AsyncSession, product_id: str) -> SuccessResponse:
        stmt = update(ProductBase).where(ProductBase.id == product_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=product_id)

    async def bulk_delete(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        """Elite V2.2: Atomic Bulk Delete (Delegated)."""
        return await bulk_delete_logic(db_session, ids)

    async def bulk_activate(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        """Elite V2.2: Atomic Bulk Activate (Delegated)."""
        return await bulk_activate_logic(db_session, ids)

    async def bulk_update(self, db_session: AsyncSession, ids: List[str], data: UpdateProductRequest) -> BulkActionResponse:
        """Elite V2.2: Atomic Bulk Update (Delegated)."""
        return await bulk_update_logic(db_session, ids, data)

    async def suggest_seo(self, name: str, description: str) -> Dict[str, str]:
        """Elite V2.2: AI SEO Suggestion (Delegated)."""
        return await suggest_seo_logic(name, description)

    async def suggest_faqs(self, name: str, description: str) -> List[Dict[str, str]]:
        """Elite V2.2: XOHI Auto FAQ Generator (Delegated)."""
        return await suggest_faqs_logic(name, description)

    async def suggest_ingredients(self, name: str, ingredients: str) -> List[Dict[str, str]]:
        """Elite V2.2: XOHI Auto Ingredients Extractor (Delegated)."""
        return await suggest_ingredients_logic(name, ingredients)

    async def suggest_specs(self, raw_text: str) -> Dict[str, str]:
        """Elite V2.2: XOHI Auto Specifications Extractor (Delegated)."""
        return await suggest_specs_logic(raw_text)

    async def suggest_semantic(self, name: str, description: str) -> str:
        """GEO 2026: XOHI Auto Semantic SGE Highlights Generator (Delegated)."""
        return await suggest_semantic_logic(name, description)

    async def suggest_ingredients_grouped(self, ingredients_text: str) -> list:
        """GEO 2026: XOHI Ingredients Grouper — nhóm hóa bảng thành phần theo chức năng (Delegated)."""
        return await suggest_ingredients_grouped_logic(ingredients_text)

    async def sync_market_price(self, db_session: AsyncSession, product_id: str) -> Dict[str, object]:
        """Elite V2.2: Market Price Intel Sync (1/Day)."""
        from backend.services.commerce.price_agent import scan_product_price

        # 1. Fetch product
        stmt = select(ProductBase).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
        product = (await db_session.execute(stmt)).scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Product {product_id} not found")

        # 2. Rate Limit: 1/day (Bản Elite V2.2: Tạm thời tắt để Sếp test ngay lập tức các thay đổi)
        # today = datetime.now(timezone.utc).date()
        # if product.last_market_sync and product.last_market_sync.date() == today:
        #     return product.market_data or {}

        # 3. Call AI
        intel = await scan_product_price(product.name)

        # 4. Update DB
        data = intel.model_dump()
        product.market_data = data
        product.last_market_sync = datetime.now(timezone.utc)

        await db_session.commit()
        return data

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_product_service(vector_service: ProductVectorService) -> ProductService:
    """Standard Litestar Provider for ProductService."""
    return ProductService(vector_service=vector_service)
