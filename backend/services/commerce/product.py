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
from sqlalchemy.dialects.postgresql import JSONB
import re
import json
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

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
        import os
        from datetime import datetime
        try:
            g_by_count = int(os.getenv("G_BY_COUNT", "0"))
        except:
            g_by_count = 0
            
        # 🎯 Elite FOMO Logic: Hourly Growth + Unique Product Offset
        now = datetime.now()
        hour_factor = now.hour * 2
        min_factor = now.minute // 15
        
        # Unique deterministic offset per product (500 to 8000 range)
        # This prevents all products from having the same sales number
        pid_str = str(row_dict.get("id", ""))
        unique_offset = (abs(hash(pid_str)) % 150) * 50 # Variates by up to 7500
        
        fomo_boost = hour_factor + min_factor + unique_offset
        
        raw_count = int(row_dict.get("order_count") or 0)
        total_boosted_count = raw_count + g_by_count + fomo_boost
        
        row_dict["order_count_text"] = self._get_display_order_count_text(row_dict.get("metadata", {}), raw_count + fomo_boost)
        row_dict["order_count"] = total_boosted_count

    def _get_display_order_count_text(self, metadata: Dict[str, object], actual_count: int) -> str:
        """Combine real orders with social proof base from metadata (Vietnamese Format)."""
        import os
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
        """
        Elite V2.2: dynamic hydration from promotion.py
        If product links to a voucher, fetch viral config from voucher.metadata_json
        """
        metadata = row_dict.get("metadata", {})
        share_promo = metadata.get("share_promotion")
        
        if not isinstance(share_promo, dict) or not share_promo.get("enabled"):
            return
            
        voucher_id = share_promo.get("voucher_id")
        if not voucher_id:
            return
            
        from backend.database.models.promotion import Voucher
        stmt = select(Voucher).where(Voucher.id == voucher_id)
        res = await db_session.execute(stmt)
        voucher = res.scalar_one_or_none()
        
        if voucher and voucher.metadata_json:
            v_config = voucher.metadata_json.get("viral_suite")
            if isinstance(v_config, dict):
                # Elite V2.2: The "Config chính thống" - Zero Hardcode
                metadata["viral_suite"] = {
                    "enabled": v_config.get("enabled", False),
                    "voucher_id": voucher_id,
                    "share_target": v_config.get("share_target", 10),
                    "share_reward_label": v_config.get("voucher_label", ""),
                    "share_cta": v_config.get("cta_text", ""),
                    "share_text": v_config.get("share_text", ""),
                    "share_count": metadata.get("share_count", 0),
                    "likes_count": metadata.get("likes", 0)
                }
                
                # Override share_promotion fields
                share_promo.update({
                    "voucher_label": v_config.get("voucher_label", share_promo.get("voucher_label")),
                    "cta_text": v_config.get("cta_text", share_promo.get("cta_text")),
                    "share_text": v_config.get("share_text", share_promo.get("share_text")),
                })
                
                # Override top-level target/reward for progress bar
                if "share_target" in v_config:
                    metadata["share_target"] = v_config["share_target"]
                if "reward_label" in v_config:
                    metadata["share_reward_label"] = v_config["reward_label"]

                # Compatibility with legacy 'viral_suite' object if present
                if "viral_suite" in metadata and isinstance(metadata["viral_suite"], dict):
                    metadata["viral_suite"].update({
                        "share_target": v_config.get("share_target", metadata["viral_suite"].get("share_target")),
                        "share_reward_label": v_config.get("reward_label", metadata["viral_suite"].get("share_reward_label")),
                    })
                    if "share_promotion" in metadata["viral_suite"]:
                         metadata["viral_suite"]["share_promotion"].update(share_promo)

    def _sanitize_vouchers(self, row_dict: ProductRowDict) -> None:
        """
        Elite V2.2: Anti-Leakage Protocol.
        Lọc bỏ các Voucher Viral khỏi metadata công khai để tránh người dùng 'soi' được mã khi chưa share.
        Các mã này chỉ được tiết lộ qua luồng verify-share chính thống.
        """
        metadata = row_dict.get("metadata")
        if not isinstance(metadata, dict):
            return
            
        vouchers = metadata.get("vouchers")
        if not isinstance(vouchers, list):
            return
            
        share_promo = metadata.get("share_promotion")
        promo_v_id = share_promo.get("voucher_id") if isinstance(share_promo, dict) else None
        
        filtered = []
        for v in vouchers:
            v_id = str(v.get("id", "")).upper()
            v_label = str(v.get("label", "")).upper()
            
            # Kiểm tra ID hoặc Nhãn chứa từ khóa nhạy cảm
            is_viral = (promo_v_id and str(v.get("id", "")) == promo_v_id) or \
                       "VIRAL" in v_id or \
                       "LAN TOA" in v_id or \
                       "LAN TỎA" in v_id or \
                       "LAN TOA" in v_label or \
                       "LAN TỎA" in v_label
            
            if not is_viral:
                filtered.append(v)
        
        metadata["vouchers"] = filtered

    async def list_products(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        featured_only: bool = False,
        category_slug: Optional[str] = None,
        category_id: Optional[str] = None,
        brand: Optional[str] = None,
        origin: Optional[str] = None,
        product_ids: Optional[List[str]] = None,
    ) -> ProductListResponse:

        """
        Elite V3.0: Hybrid Viral Search Engine.
        Combines Keyword Recall + Semantic Intent + Social Proof (Heat Ranking).
        """
        conditions = [ProductBase.deleted_at == None]
        # Elite V2.2: Enforce dynamic tenant isolation (Rule R03)
        from backend.database import current_tenant_id
        from backend.constants.tenants import DEFAULT_TENANT_ID
        tid = current_tenant_id.get() or DEFAULT_TENANT_ID
        conditions.append(ProductBase.tenant_id == tid)
        
        # Elite V2.2: Chỉ lọc tồn kho cho Client Storefront (khi status="ACTIVE")
        # Admin Panel cần thấy mọi sản phẩm để quản lý (kể cả khi hết hàng)
        if status == "ACTIVE":
            conditions.append(ProductBase.stock > 0)
        
        if status and status != "all":
            conditions.append(ProductBase.status == status.upper())
        if featured_only:
            conditions.append(ProductBase.is_ai_featured == True)
        if category_slug:
            # Filter sản phẩm theo category slug (join Category)
            conditions.append(Category.slug == category_slug)
        if category_id:
            conditions.append(ProductBase.category_id == category_id)
        if brand:
            brand_safe = escape_like(brand)
            conditions.append(or_(
                ProductBase.product_metadata["brand"].astext.ilike(f"%{brand_safe}%"),
                ProductBase.attributes["brand"].astext.ilike(f"%{brand_safe}%"),
                ProductBase.attributes["Thương hiệu"].astext.ilike(f"%{brand_safe}%")
            ))
        if origin:
            origin_safe = escape_like(origin)
            conditions.append(or_(
                ProductBase.product_metadata["origin"].astext.ilike(f"%{origin_safe}%"),
                ProductBase.attributes["origin"].astext.ilike(f"%{origin_safe}%"),
                ProductBase.attributes["Xuất xứ"].astext.ilike(f"%{origin_safe}%")
            ))
        if product_ids:
            conditions.append(ProductBase.id.in_(product_ids))


        # 🎯 CASE 1: SEARCH OVERRIDE (Hybrid Strategy)
        if search:
            safe = escape_like(search)
            
            # --- LAYER 1: KEYWORD RECALL (Primary for SKU/Prefix) ---
            keyword_stmt = select(
                ProductBase.id, ProductBase.name, ProductBase.sku,
                ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
                ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
                ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
                ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
                ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
                ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
                Category.name.label("category_name"), Category.slug.label("category_slug")
            ).outerjoin(Category, ProductBase.category_id == Category.id).where(
                and_(*conditions),
                or_(
                    func.unaccent(ProductBase.name).ilike(func.unaccent(f"%{safe}%")),
                    ProductBase.sku.ilike(f"%{safe}%"),
                )
            ).limit(limit * 2) # Overfetch for ranking
            
            keyword_results = (await db_session.execute(keyword_stmt)).mappings().all()
            
            # --- LAYER 2: SEMANTIC RECALL (Intent Matching) ---
            semantic_results = await self.vector_service.search_semantic(db_session, search, limit=limit)
            semantic_ids = [r["id"] for r in semantic_results]
            
            # --- LAYER 3: VIRAL HEAT SCORING ---
            final_map: Dict[str, Dict[str, object]] = {}
            
            # Process Keywords
            search_low = search.lower().strip()
            for r in keyword_results:
                pid = str(r["id"])
                name_low = r["name"].lower()
                
                # Elite V3.0 Rank Matrix: Exact Match Wins Total
                if search_low == name_low:
                    relevance = 5.0  # Absolute Peak Priority
                elif name_low.startswith(search_low):
                    relevance = 1.2  # Prefix Match
                elif search_low in name_low:
                    relevance = 0.8  # Fuzzy Keyword Match
                else:
                    relevance = 0.5
                
                # SKU Match Override
                if r["sku"] and search_low == r["sku"].lower().strip():
                    relevance = 5.0
                
                final_map[pid] = {**r, "score": relevance}

            # Process Semantic (Merge & Boost)
            # STEP 1: Collect IDs that are semantic-only (not in keyword results)
            semantic_only_ids: List[str] = []
            semantic_score_map: Dict[str, float] = {}
            for r in semantic_results:
                pid = str(r["id"])
                score = float(r["match_score"])
                semantic_score_map[pid] = score
                if pid in final_map:
                    # Combined Vector Boost (Avoid overriding Exact Match)
                    if final_map[pid]["score"] < 2.0:
                        final_map[pid]["score"] = max(float(final_map[pid]["score"]), score) + 0.2
                else:
                    semantic_only_ids.append(pid)

            # STEP 2: Batch fetch all semantic-only products in ONE query (Anti N+1)
            if semantic_only_ids:
                batch_stmt = select(
                    ProductBase.id, ProductBase.name, ProductBase.sku,
                    ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
                    ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
                    ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
                    ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
                    ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
                    ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
                    Category.name.label("category_name"), Category.slug.label("category_slug")
                ).outerjoin(Category, ProductBase.category_id == Category.id).where(
                    ProductBase.id.in_(semantic_only_ids)
                )
                batch_results = (await db_session.execute(batch_stmt)).mappings().all()
                for full_r in batch_results:
                    pid = str(full_r["id"])
                    final_map[pid] = {**full_r, "score": semantic_score_map.get(pid, 0.5)}

            # --- LAYER 4: VIRAL BOOST SCORING ---
            import math
            ranked_list = []
            for pid, p in final_map.items():
                order_count = int(p.get("order_count") or 0)
                is_viral = bool(p.get("is_ai_featured") or False)
                # Boost based on sales volume and viral status
                social_boost = math.log10(order_count + 1) * 0.15
                viral_boost = 0.2 if is_viral else 0.0
                
                p["final_rank"] = float(p["score"]) + social_boost + viral_boost
                ranked_list.append(p)

            # --- LAYER 5: FINALIZE RESULT ---
            ranked_list.sort(key=lambda x: x["final_rank"], reverse=True)
            subset = ranked_list[offset : offset + limit]
            
            data: List[ProductResponse] = []
            for row_mapping in subset:
                row_dict: ProductRowDict = dict(row_mapping) # type: ignore
                row_dict["variants"] = []
                self._inject_marketing_boost(row_dict)
                await self._hydrate_viral_config(db_session, row_dict)
                self._sanitize_vouchers(row_dict)
                data.append(ProductResponse.model_validate(row_dict))

            # --- LAYER 6: COMPUTE FACETS (Elite V2.2 Dynamic Filters) ---
            facet_brands: set[str] = set()
            facet_origins: set[str] = set()
            prices: List[float] = []
            for p in ranked_list:
                price_val = float(p.get("price") or 0)
                if price_val > 0:
                    prices.append(price_val)
                attrs = p.get("attributes")
                if isinstance(attrs, dict):
                    b = attrs.get("brand") or attrs.get("Thương hiệu")
                    if isinstance(b, str) and b.strip():
                        facet_brands.add(b.strip())
                    o = attrs.get("origin") or attrs.get("Xuất xứ")
                    if isinstance(o, str) and o.strip():
                        facet_origins.add(o.strip())

            facets = SearchFacets(
                brands=sorted(facet_brands),
                origins=sorted(facet_origins),
                price_min=min(prices) if prices else 0.0,
                price_max=max(prices) if prices else 0.0,
            )

            return ProductListResponse(data=data, total=len(ranked_list), facets=facets)

        # 🎯 CASE 2: STANDARD LISTING
        # 1. COUNT (Zero-Hydration)
        count_stmt = select(func.count(ProductBase.id))
        if category_slug:
            count_stmt = count_stmt.outerjoin(Category, ProductBase.category_id == Category.id)
        
        count_stmt = count_stmt.where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # 2. R76: Scalar Projection Fetch
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
            ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
            ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
            Category.name.label("category_name"), Category.slug.label("category_slug")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(ProductBase.created_at.desc())

        result = await db_session.execute(stmt)
        data = []
        for row in result:
            row_dict: ProductRowDict = dict(row._mapping) # type: ignore
            row_dict["variants"] = []
            self._inject_marketing_boost(row_dict)
            await self._hydrate_viral_config(db_session, row_dict)
            self._sanitize_vouchers(row_dict)
            data.append(ProductResponse.model_validate(row_dict))

        return ProductListResponse(data=data, total=total)

    async def get_product(self, db_session: AsyncSession, product_id: str) -> ProductResponse:
        """Get a single product (R76: Scalar Projection)."""
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
            ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
            ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
            Category.name.label("category_name"), Category.slug.label("category_slug")
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

        # Elite Dynamic Counting & Marketing Boost
        self._inject_marketing_boost(row_dict)
        await self._hydrate_viral_config(db_session, row_dict)
        self._sanitize_vouchers(row_dict)

        return ProductResponse.model_validate(row_dict)

    async def get_product_by_slug(self, db_session: AsyncSession, slug: str) -> ProductResponse:
        """Get a single product by slug (R76: Scalar Projection)."""
        # Normalize slug: remove trailing slashes to prevent 404 on clean URL variants
        slug = slug.rstrip('/')
        # Elite V2.2: Tenant Isolation Protocol
        tid = current_tenant_id.get()
        
        stmt = select(
            ProductBase.id, ProductBase.name, ProductBase.sku,
            ProductBase.price, ProductBase.discount_price, ProductBase.stock, ProductBase.status,
            ProductBase.category_id, ProductBase.short_description, ProductBase.description, ProductBase.type,
            ProductBase.slug, ProductBase.seo_title, ProductBase.seo_description, ProductBase.seo_keywords,
            ProductBase.images, ProductBase.mobile_images, ProductBase.attributes, ProductBase.tier_variations, 
            ProductBase.product_metadata.label("metadata"), ProductBase.market_data, ProductBase.last_market_sync,
            ProductBase.created_at, ProductBase.order_count, ProductBase.is_ai_featured,
            Category.name.label("category_name"), Category.slug.label("category_slug"), Category.slug.label("category_slug")
        ).outerjoin(Category, ProductBase.category_id == Category.id).where(
            ProductBase.deleted_at == sa.null()
        )

        # 1. Try Exact Match (Primary)
        res = await db_session.execute(stmt.where(
            ProductBase.slug == slug,
            ProductBase.tenant_id == tid if tid else sa.true()
        ))
        row = res.first()

        # 2. Robust Fallback: Try slugified name match if direct slug fails (Elite Reconstruction)
        if not row:
            from backend.utils.text import slugify
            # Search by name-based slug if the current slug might be legacy/truncated
            res = await db_session.execute(stmt.where(
                sa.func.lower(ProductBase.name).like(f"%{slug.split('-')[0]}%"), # Heuristic prefix optimization
                ProductBase.tenant_id == tid if tid else sa.true()
            ))
            candidates = res.all()
            for cand in candidates:
                if slugify(cand.name) == slug:
                    row = cand
                    break

        if not row and not tid:
             res = await db_session.execute(stmt.where(ProductBase.slug == slug))
             row = res.first()

        if not row:
            logger.debug(f"[ProductService] Product with slug '{slug}' not found in DB")
            raise NotFoundException(f"Product with slug '{slug}' not found")

        product_id = row.id
        # Fetch variants
        v_stmt = select(ProductVariant).where(ProductVariant.product_base_id == product_id, ProductVariant.deleted_at == None)
        variants = (await db_session.execute(v_stmt)).scalars().all()

        row_dict: ProductRowDict = dict(row._mapping) # type: ignore
        row_dict["variants"] = list(variants)

        # Elite Dynamic Counting & Marketing Boost
        self._inject_marketing_boost(row_dict)
        await self._hydrate_viral_config(db_session, row_dict)
        self._sanitize_vouchers(row_dict)

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
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_activate(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(status="ACTIVE")
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_update(self, db_session: AsyncSession, ids: List[str], data: UpdateProductRequest) -> BulkActionResponse:
        """Elite V2.2: Atomic Bulk Update for Products."""
        # Convert Pydantic data to dict, excluding unset fields
        update_data = data.model_dump(exclude_unset=True, by_alias=False)

        # Mapping frontend camelCase/Pydantic fields to SQLAlchemy snake_case
        # Note: model_dump(by_alias=False) gives us the field names, but we need to ensure
        # they match the ProductBase columns (mostly snake_case).

        db_data = {}
        if "name" in update_data: db_data["name"] = update_data["name"]
        if "sku" in update_data: db_data["sku"] = update_data["sku"]
        if "price" in update_data: db_data["price"] = update_data["price"]
        if "discountPrice" in update_data: db_data["discount_price"] = update_data["discountPrice"]
        if "stock" in update_data: db_data["stock"] = update_data["stock"]
        if "status" in update_data: db_data["status"] = update_data["status"].upper()
        if "isAiFeatured" in update_data: db_data["is_ai_featured"] = update_data["isAiFeatured"]
        if "categoryId" in update_data: db_data["category_id"] = update_data["categoryId"]
        if "shortDescription" in update_data: db_data["short_description"] = update_data["shortDescription"]
        if "description" in update_data: db_data["description"] = update_data["description"]
        if "slug" in update_data: db_data["slug"] = update_data["slug"]
        if "seoTitle" in update_data: db_data["seo_title"] = update_data["seoTitle"]
        if "seoDescription" in update_data: db_data["seo_description"] = update_data["seoDescription"]
        if "seoKeywords" in update_data: db_data["seo_keywords"] = update_data["seoKeywords"]
        if "images" in update_data: db_data["images"] = update_data["images"]
        if "mobileImages" in update_data: db_data["mobile_images"] = update_data["mobileImages"]
        if "attributes" in update_data: db_data["attributes"] = update_data["attributes"]
        if "metadata" in update_data: db_data["product_metadata"] = update_data["metadata"]
        if "tierVariations" in update_data: db_data["tier_variations"] = update_data["tierVariations"]

        if not db_data:
            return BulkActionResponse(ok=True, count=0)

        stmt = update(ProductBase).where(ProductBase.id.in_(ids)).values(**db_data)
        await db_session.execute(stmt)

        # If name or description changed, embeddings might need update, but for bulk
        # it's usually AI Featured or Discount, so we skip vector sync here to save O(N) cost
        # unless explicitly requested.

        return BulkActionResponse(ok=True, count=len(ids))

    async def suggest_seo(self, name: str, description: str) -> Dict[str, str]:
        """Elite V2.2: AI SEO Suggestion (C.O.R.E Engine)."""
        agent = Agent(
            system_prompt=(
                "Bạn là chuyên gia SEO hàng đầu Việt Nam. Hãy tối ưu tiêu đề, mô tả và từ khóa SEO cho sản phẩm này. "
                "QUY TẮC TỐI CAO: Dù tên sản phẩm hoặc mô tả đầu vào là tiếng Anh, bạn BẮT BUỘC phải phản hồi nội dung hoàn toàn bằng tiếng Việt thuần 100%. "
                "Nội dung phải súc tích, hấp dẫn và chuẩn SEO. "
                "Chỉ trả về JSON hợp lệ, không có markdown: "
                "{\"title\": \"...\", \"description\": \"...\", \"keywords\": \"...\"}"
            )
        )
        prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"
        
        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=30.0
            )
            
            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\{.*\}', suggested_json_str, re.DOTALL)
                parsed = json.loads(match.group(0)) if match else {"title": "", "description": "", "keywords": ""}
                return parsed
            
            return {"title": f"{name} Chính Hãng", "description": "Sản phẩm chính hãng", "keywords": ""}
            
        except Exception as e:
            logger.exception(f"[ProductService] AI SEO Suggestion Failed: {e}")
            return {"title": f"{name} Chính Hãng", "description": "Mua sản phẩm chính hãng với nhiều ưu đãi", "keywords": ""}

    async def suggest_faqs(self, name: str, description: str) -> List[Dict[str, str]]:
        """Elite V2.2: XOHI Auto FAQ Generator."""
        agent = Agent(
            system_prompt=(
                "Bạn là chuyên gia tư vấn sản phẩm. Dựa trên tên và mô tả sản phẩm, hãy tạo từ 3 đến 5 câu hỏi thường gặp và câu trả lời ngắn gọn, hữu ích bằng tiếng Việt. "
                "QUY TẮC TỐI CAO: Dù tên sản phẩm đầu vào là tiếng Anh, toàn bộ câu hỏi và câu trả lời phải là tiếng Việt thuần 100%. "
                "Chỉ trả về mảng JSON chính xác các đối tượng, không có markdown: "
                "[{\"question\": \"...\", \"answer\": \"...\"}]"
            )
        )
        prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"

        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=45.0
            )

            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\[.*\]', suggested_json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        return parsed

            return []

        except Exception as e:
            logger.exception(f"[ProductService] AI FAQ Suggestion Failed: {e}")
            return []

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
