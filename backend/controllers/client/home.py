from __future__ import annotations
import logging
import json
import os
from datetime import datetime
from litestar import Controller, get, post, Request
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

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
from backend.services.xohi_memory import xohi_memory
from backend.schemas.common import SuccessResponse

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
        request: Request,
        layout_only: bool = False
    ) -> HomeDataResponse:
        """PUBLIC: Get aggregated data for the home page."""
        # Detect device type
        user_agent = request.headers.get("user-agent", "").lower()
        is_mobile = any(m in user_agent for m in ["mobile", "android", "iphone", "ipad"])

        # Check Redis Cache (Elite V2.2)
        cache_key = f"support:client_home:{'layout_' if layout_only else ''}{'mobile' if is_mobile else 'desktop'}"
        try:
            if xohi_memory._use_redis and xohi_memory.client:
                cached_data = await xohi_memory.client.get(cache_key)
                if cached_data:
                    return HomeDataResponse.model_validate_json(cached_data)
        except Exception as cache_exc:
            logger.warning(f"⚠️ [ClientHomeController] Redis cache read failed: {cache_exc}")

        # 1. Fetch system settings for shop info (Elite V2.2)
        system_settings = await settings_service.get_general_settings(db_session)
        
        # 2. Fetch banners & categories
        categories_resp = await category_service.list_categories(db_session)
        
        if categories_resp:
            full_list = categories_resp.data
            if is_mobile:
                filtered_cats = [c for c in full_list if c.showOnMobile is not False]
            else:
                filtered_cats = [c for c in full_list if c.showOnDesktop is not False]
        else:
            filtered_cats = []
 
        banners = await banner_service.list_banners(db_session, active_only=True)

        # 3. Fetch heavy data only when not layout_only (Elite Performance optimization)
        products_list = []
        ai_products = []
        vouchers_list = []

        if not layout_only:
            all_products = await product_service.list_products(db_session, limit=24, offset=0, status="ACTIVE", is_public=True)
            products_list = [p for p in all_products.data] if all_products else []

            vouchers_resp = await promotion_service.list_vouchers(db_session, is_active=True, exclude_viral=True, limit=20)
            vouchers_list = [v for v in vouchers_resp.data] if vouchers_resp else []

            ai_products_resp = await product_service.list_products(db_session, limit=10, offset=0, status="ACTIVE", featured_only=True, is_public=True)
            ai_products = ai_products_resp.data if ai_products_resp else []

        # 4. Generate SEO Metadata (Elite V2.2)
        seo_meta = None
        if system_settings and system_settings.settings:
            settings = system_settings.settings
            await SeoService._resolve_settings(db_session)
            seo_meta = SeoService.generate_home_seo_meta(
                title=settings.seo_analytics.meta_title,
                description=settings.seo_analytics.meta_description,
                keywords=settings.seo_analytics.meta_keywords,
                site_name=settings.basic_info.site_name
            )

        # Format response
        response_data = HomeDataResponse(
            banners=[b for b in banners.data] if banners else [],
            categories=filtered_cats,
            products=products_list,
            ai_products=ai_products,
            vouchers=vouchers_list,
            settings=system_settings.settings if system_settings else SystemSettingsPayload(),
            seo_meta=seo_meta,
            videos=[]
        )

        # Save to Redis Cache (TTL = 60 seconds)
        try:
            if xohi_memory._use_redis and xohi_memory.client:
                await xohi_memory.client.set(cache_key, response_data.model_dump_json(), ex=60)
        except Exception as cache_exc:
            logger.warning(f"⚠️ [ClientHomeController] Redis cache set failed: {cache_exc}")

        return response_data

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

    @post("/report-error")
    async def report_client_error(self, request: Request, data: Dict) -> SuccessResponse:
        """
        [SOC] Báo cáo lỗi kết nối/timeout từ Frontend và gửi Telegram alert.
        """
        from backend.services.telegram_service import telegram_service
        import html

        error_type = data.get("error", "UNKNOWN_ERROR")
        url = data.get("url", "N/A")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        details = data.get("details", "")
        
        ip = (
            request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
            or "unknown"
        )

        message = (
            f"🚨 <b>[SOC ALERT] SỰ CỐ KẾT NỐI HỆ THỐNG</b>\n"
            f"🔴 <b>Lỗi:</b> {html.escape(error_type)}\n"
            f"🔗 <b>Endpoint:</b> {html.escape(url)}\n"
            f"🌐 <b>IP Khách:</b> {html.escape(ip)}\n"
            f"⏱️ <b>Thời gian:</b> {html.escape(timestamp)}\n"
            f"📝 <b>Chi tiết:</b> {html.escape(details)}\n"
            f"💡 <i>Khuyến nghị: Kiểm tra trạng thái tải của hệ thống.</i>"
        )
        
        # 1. Ghi log audit an ninh
        logger.error(f"❌ [SOC SYSTEM ERROR] {error_type} on {url} - client: {ip}")
        audit_log_path = "logs/audit.log"
        try:
            os.makedirs("logs", exist_ok=True)
            with open(audit_log_path, "a") as f:
                log_entry = {
                    "timestamp": timestamp,
                    "action": "SYSTEM_CONNECTION_FAILED",
                    "actor": "CLIENT_TELEMETRY",
                    "ip": ip,
                    "suspicious": True,
                    "details": f"{error_type} on {url}: {details}"
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as log_err:
            logger.error(f"❌ [SOC] Failed to write connection error to audit log: {log_err}")

        # 2. Gửi Telegram alert
        await telegram_service.send_alert(message)
        
        return SuccessResponse(message="Đã nhận báo cáo sự cố thành công.")
