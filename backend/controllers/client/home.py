from __future__ import annotations
import logging
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.category import CategoryService, provide_category_service

from backend.services.commerce.product_vector import ProductVectorService, provide_product_vector_service

logger = logging.getLogger("api-gateway")

class ClientHomeController(Controller):
    """Elite V2.2: Public Home Controller for Client Storefront."""
    path = "/api/v1/client/home"
    dependencies = {
        "product_service": Provide(provide_product_service),
        "category_service": Provide(provide_category_service),
        "vector_service": Provide(provide_product_vector_service),
    }

    @get("/")
    async def get_home_data(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        category_service: CategoryService
    ) -> Dict[str, Any]:
        """PUBLIC: Get aggregated data for the home page."""
        # Fetch actual products and categories
        products = await product_service.list_products(db_session, limit=10, offset=0, status="ACTIVE")
        categories = await category_service.list_categories(db_session)
        
        # Format response to match SvelteKit expectation
        return {
            "banners": [],  # Banners can be fetched from a banner service later
            "categories": [c.model_dump() for c in categories.data] if categories else [],
            "products": [p.model_dump() for p in products.data] if products else [],
            "videos": []    # Videos can be fetched from a media service later
        }
