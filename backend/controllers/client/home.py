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

logger = logging.getLogger("api-gateway")

class ClientHomeController(Controller):
    """Elite V2.2: Public Home Controller for Client Storefront."""
    path = "/api/v1/client/home"
    dependencies = {
        "product_service": Provide(provide_product_service),
        "category_service": Provide(provide_category_service),
        "vector_service": Provide(provide_product_vector_service),
        "banner_service": Provide(provide_banner_service),
    }

    @get("/")
    async def get_home_data(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        category_service: CategoryService,
        banner_service: BannerService
    ) -> Dict[str, Any]:
        """PUBLIC: Get aggregated data for the home page."""
        # Fetch actual products (Active only)
        all_products = await product_service.list_products(db_session, limit=100, offset=0, status="ACTIVE")
        categories = await category_service.list_categories(db_session)
        banners = await banner_service.list_banners(db_session, position="home_main", active_only=True)
        
        # Elite V2.2: Separate AI Featured products for the Special Banner section
        ai_products = [p for p in all_products.data if p.isAiFeatured]
        
        # Format response to match SvelteKit expectation
        return {
            "banners": [b.model_dump() if hasattr(b, "model_dump") else b for b in banners.data] if banners else [],
            "categories": [c.model_dump() if hasattr(c, "model_dump") else c for c in categories.data] if categories else [],
            "products": [p.model_dump() if hasattr(p, "model_dump") else p for p in all_products.data] if all_products else [],
            "ai_products": [p.model_dump() if hasattr(p, "model_dump") else p for p in ai_products],
            "videos": []
        }
