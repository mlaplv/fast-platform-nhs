from __future__ import annotations
import logging
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.category import CategoryService, provide_category_service

from backend.services.commerce.product_vector import ProductVectorService, provide_product_vector_service
from backend.services.banner_service import BannerService, provide_banner_service
from backend.services.settings_service import SettingsService, provide_settings_service
from backend.services.promotion_admin_service import PromotionAdminService, promotion_admin_service
from backend.schemas.client_home import HomeDataResponse
from backend.schemas.promotion import VoucherListResponse
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
        return await promotion_service.list_vouchers(db_session, is_active=True, limit=50)

    @get("/")
    async def get_home_data(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        category_service: CategoryService,
        banner_service: BannerService,
        settings_service: SettingsService,
        promotion_service: PromotionAdminService
    ) -> HomeDataResponse:
        """PUBLIC: Get aggregated data for the home page."""
        # 1. Fetch system settings for shop info (Elite V2.2)
        system_settings = await settings_service.get_general_settings(db_session)
        
        # 2. Fetch actual products (Active only)
        all_products = await product_service.list_products(db_session, limit=100, offset=0, status="ACTIVE")
        categories = await category_service.list_categories(db_session)
        banners = await banner_service.list_banners(db_session, active_only=True)
        vouchers_resp = await promotion_service.list_vouchers(db_session, is_active=True, limit=20)

        # Elite V2.2: Optimized AI Featured fetch (R76)
        ai_products_resp = await product_service.list_products(db_session, limit=10, offset=0, status="ACTIVE", featured_only=True)
        ai_products = ai_products_resp.data

        # Format response to match HomeDataResponse schema (Elite V2.2)
        # Sếp ơi: Pass trực tiếp object để Pydantic lo phần validation/serialization, CẤM model_dump sớm.
        return HomeDataResponse(
            banners=[b for b in banners.data] if banners else [],
            categories=categories.data if categories else [],
            products=[p for p in all_products.data] if all_products else [],
            ai_products=[p for p in ai_products],
            vouchers=[v for v in vouchers_resp.data] if vouchers_resp else [],
            settings=system_settings.settings if system_settings else SystemSettingsPayload(),
            videos=[]
        )
