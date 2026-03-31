from __future__ import annotations
import logging
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.product import ProductResponse
from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.product_vector import provide_product_vector_service

logger = logging.getLogger("api-gateway")

class PublicProductController(Controller):
    """Elite V2.2: Public Product Controller for Client Funnels."""
    path = "/api/v1/client/products"
    dependencies = {
        "vector_service": Provide(provide_product_vector_service),
        "product_service": Provide(provide_product_service),
    }

    @get("/slug/{slug:str}", cache=300)
    async def get_product_by_slug(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        slug: str
    ) -> ProductResponse:
        """PUBLIC: Get a single product by slug (Scalar Projection)."""
        return await product_service.get_product_by_slug(db_session, slug)
