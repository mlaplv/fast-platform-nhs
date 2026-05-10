from __future__ import annotations
import logging
from litestar import Controller, get, Request
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.category import CategoryService, provide_category_service

from backend.services.commerce.product_vector import ProductVectorService, provide_product_vector_service
from backend.services.banner_service import BannerService, provide_banner_service
from backend.services.settings_service import SettingsService, provide_settings_service
from backend.services.promotion_admin_service import PromotionAdminService, promotion_admin_service
from backend.services.commerce.seo_service import SeoService
from backend.schemas.client_home import HomeDataResponse
from backend.schemas.promotion import VoucherListResponse
from backend.schemas.category import CategoryResponse
from backend.schemas.system_settings import SystemSettingsPayload, SystemSettingsResponse

logger = logging.getLogger("api-gateway")

async def provide_promotion_service() -> PromotionAdminService:
    """Elite V2.2: Async provider to avoid Litestar sync warnings."""
    return promotion_admin_service

class ClientHomeController(Controller):
    """Elite V2.2: Public Home Controller for Client Storefront."""
    path = "/api/v1/client/home"
    dependencies = {
        "product_service": Provide(provide_product_service),
        "category_service": Provide(provide_category_service),
        "vector_service": Provide(provide_product_vector_service),
        "banner_service": Provide(provide_banner_service),
        "settings_service": Provide(provide_settings_service),
        "promotion_service": Provide(provide_promotion_service),
    }

    @get("/vouchers")
    async def get_vouchers(
        self,
        db_session: AsyncSession,
        promotion_service: PromotionAdminService
    ) -> VoucherListResponse:
        """PUBLIC: Get active vouchers for global store synchronization."""
        return await promotion_service.list_vouchers(db_session, is_active=True, exclude_viral=True, limit=50)

    @get("/")
    async def get_home_data(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        category_service: CategoryService,
        banner_service: BannerService,
        settings_service: SettingsService,
        promotion_service: PromotionAdminService,
        request: Request
    ) -> HomeDataResponse:
        """PUBLIC: Get aggregated data for the home page."""
        # 1. Fetch system settings for shop info (Elite V2.2)
        system_settings = await settings_service.get_general_settings(db_session)
        
        # 2. Fetch actual products (Active only)
        # Elite Performance Fix P3.1: Giảm limit từ 100 xuống 24 để tối ưu tốc độ load home
        all_products = await product_service.list_products(db_session, limit=24, offset=0, status="ACTIVE")
        categories_resp = await category_service.list_categories(db_session)
        
        # Elite V2.2: Device-aware category filtering
        user_agent = request.headers.get("user-agent", "").lower()
        is_mobile = any(m in user_agent for m in ["mobile", "android", "iphone", "ipad"])
        
        if categories_resp:
            full_list = categories_resp.data
            if is_mobile:
                filtered_cats = [c for c in full_list if c.showOnMobile is not False]
            else:
                filtered_cats = [c for c in full_list if c.showOnDesktop is not False]
        else:
            filtered_cats = []

        banners = await banner_service.list_banners(db_session, active_only=True)
        vouchers_resp = await promotion_service.list_vouchers(db_session, is_active=True, exclude_viral=True, limit=20)

        # Elite V2.2: Optimized AI Featured fetch (R76)
        ai_products_resp = await product_service.list_products(db_session, limit=10, offset=0, status="ACTIVE", featured_only=True)
        ai_products = ai_products_resp.data if ai_products_resp else []

        # 3. Generate SEO Metadata (Elite V2.2)
        seo_meta = None
        if system_settings and system_settings.settings:
            settings = system_settings.settings
            seo_meta = SeoService.generate_home_seo_meta(
                title=settings.seo_analytics.meta_title,
                description=settings.seo_analytics.meta_description,
                keywords=settings.seo_analytics.meta_keywords,
                site_name=settings.basic_info.site_name
            )

        # Format response
        return HomeDataResponse(
            banners=[b for b in banners.data] if banners else [],
            categories=filtered_cats,
            products=[p for p in all_products.data] if all_products else [],
            ai_products=[p for p in ai_products],
            vouchers=[v for v in vouchers_resp.data] if vouchers_resp else [],
            settings=system_settings.settings if system_settings else SystemSettingsPayload(),
            seo_meta=seo_meta,
            videos=[]
        )

    @get("/category/{slug:str}")
    async def get_category_by_slug(
        self,
        db_session: AsyncSession,
        category_service: CategoryService,
        slug: str
    ) -> CategoryResponse:
        """PUBLIC: Verify category slug for URL validation (Elite V2.2)."""
        res = await category_service.get_category_by_slug(db_session, slug)
        if not res:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Category slug '{slug}' not found")
        return res
