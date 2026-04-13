from __future__ import annotations
import logging
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.schemas.product import ProductResponse, ProductListResponse
from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.product_vector import provide_product_vector_service
from backend.services.commerce.seo_service import SeoService

logger = logging.getLogger("api-gateway")

class PublicProductController(Controller):
    """Elite V2.2: Public Product Controller for Client Funnels."""
    path = "/api/v1/client/products"
    dependencies = {
        "vector_service": Provide(provide_product_vector_service),
        "product_service": Provide(provide_product_service),
    }

    @get("/")
    async def get_products(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        featured_only: bool = False,
        category_slug: Optional[str] = None,
    ) -> ProductListResponse:
        """PUBLIC: List products. Supports filter by category_slug."""
        return await product_service.list_products(
            db_session,
            limit=limit,
            offset=offset,
            status="ACTIVE",
            search=search,
            featured_only=featured_only,
            category_slug=category_slug,
        )

    @get("/slug/{slug:str}")
    async def get_product_by_slug(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        slug: str
    ) -> ProductResponse:
        """PUBLIC: Get a single product by slug (Scalar Projection)."""
        product = await product_service.get_product_by_slug(db_session, slug)
        product.seoMeta = SeoService.generate_seo_meta(product)
        return product
