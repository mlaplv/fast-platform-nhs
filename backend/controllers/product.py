from __future__ import annotations
import logging
from typing import List, Dict, Union, Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import ProductBaseRepository, provide_product_repo
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.product import (
    CreateProductRequest,
    UpdateProductRequest,
    ProductResponse,
    ProductListResponse,
    BulkUpdateProductRequest
)
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.product_vector import ProductVectorService, provide_product_vector_service

logger = logging.getLogger("api-gateway")

class ProductController(Controller):
    """R2: Class-based Litestar Controller for Product CRUD."""
    path = "/api/v1/products"
    guards = [PermissionGuard(PermissionEnum.PRODUCT_READ)]
    dependencies = {
        "prod_repo": Provide(provide_product_repo),
        "vector_service": Provide(provide_product_vector_service),
        "product_service": Provide(provide_product_service),
    }

    @get("/", guards=[PermissionGuard(PermissionEnum.PRODUCT_READ)])
    async def list_products(
        self, 
        db_session: AsyncSession,
        product_service: ProductService,
        limit: int = 20, 
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        featured_only: bool = False,
        cursor: Optional[str] = None,
    ) -> ProductListResponse:
        """List products (R76: Scalar Projection). R41: N+1 Safe."""
        return await product_service.list_products(
            db_session=db_session,
            limit=limit,
            offset=offset,
            status=status,
            search=search,
            category_id=category_id,
            featured_only=featured_only,
            cursor=cursor,
        )

    @get("/{product_id:str}", guards=[PermissionGuard(PermissionEnum.PRODUCT_READ)])
    async def get_product(
        self, 
        db_session: AsyncSession, 
        product_service: ProductService,
        product_id: str
    ) -> ProductResponse:
        """Get a single product (R76: Scalar Projection)."""
        return await product_service.get_product(db_session, product_id)

    @post("/", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def create_product(
        self, 
        db_session: AsyncSession, 
        product_service: ProductService,
        data: CreateProductRequest
    ) -> SuccessResponse:
        """Create a new product (Service-Centric RAG)."""
        res = await product_service.create_product(db_session, data)
        await db_session.commit()
        return res

    @patch("/{product_id:str}", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def update_product(
        self, 
        db_session: AsyncSession, 
        product_service: ProductService,
        product_id: str, 
        data: UpdateProductRequest
    ) -> SuccessResponse:
        """Update a product (Service-Centric RAG)."""
        # Elite V2.2: Pure dependency injection
        if data.description is not None:
            logger.info(f"📥 [ProductController] PATCH {product_id} received description. Len: {len(data.description)}")
        res = await product_service.update_product(db_session, product_id, data)
        await db_session.commit()
        return res

    @delete("/{product_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def delete_product(
        self, 
        db_session: AsyncSession, 
        product_service: ProductService,
        product_id: str
    ) -> SuccessResponse:
        """R18: Soft delete."""
        res = await product_service.delete_product(db_session, product_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def bulk_delete(
        self, 
        db_session: AsyncSession, 
        product_service: ProductService,
        data: BulkIdsRequest
    ) -> BulkActionResponse:
        """R18: Soft delete multiple products."""
        res = await product_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-activate", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def bulk_activate(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        data: BulkIdsRequest
    ) -> BulkActionResponse:
        """Activate multiple products."""
        res = await product_service.bulk_activate(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-update", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def bulk_update(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        data: BulkUpdateProductRequest
    ) -> BulkActionResponse:
        """Elite V2.2: Update multiple products fields in one transaction."""
        res = await product_service.bulk_update(db_session, data.ids, data.data)
        await db_session.commit()
        return res

    @post("/faq-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
    async def suggest_faqs(
        self,
        product_service: ProductService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto FAQ Generator for Products."""
        name = data.get("name", "")
        description = data.get("description", "")
        faqs = await product_service.suggest_faqs(name, description)
        return {"data": faqs}

    @post("/ingredients-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
    async def suggest_ingredients(
        self,
        product_service: ProductService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto Ingredients Extractor for Products."""
        name = data.get("name", "")
        ingredients = data.get("ingredients", "")
        result = await product_service.suggest_ingredients(name, ingredients)
        return {"data": result}

    @post("/specs-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
    async def suggest_specs(
        self,
        product_service: ProductService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto Specs Extractor for Products."""
        raw_text = data.get("raw_text", "")
        result = await product_service.suggest_specs(raw_text)
        return {"data": result}

    @post("/semantic-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
    async def suggest_semantic(
        self,
        product_service: ProductService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto Semantic SGE Highlights Generator for Products."""
        name = data.get("name", "")
        description = data.get("description", "")
        seo_description = data.get("seo_description", "")
        result = await product_service.suggest_semantic(name, description, seo_description)
        return {"data": result}

    @post("/ingredients-grouped", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
    async def suggest_ingredients_grouped(
        self,
        product_service: ProductService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Ingredients Grouper — phân loại thành phần cosmetic theo nhóm và độ ưu tiên."""
        ingredients_text = data.get("ingredients", "")
        result = await product_service.suggest_ingredients_grouped(ingredients_text)
        return {"data": result}


    @post("/seo-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def suggest_seo(
        self,
        product_service: ProductService,
        data: Dict[str, str]
    ) -> SuccessResponse:
        """AI Suggestion for SEO metadata (Elite V2.2: Service-Centric)."""
        res_data = await product_service.suggest_seo(
            name=data.get("name", ""),
            description=data.get("description", "")
        )
        return SuccessResponse(message="Thành công", data=res_data)

    @post("/{product_id:str}/sync-market", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def sync_market_price(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        product_id: str
    ) -> SuccessResponse:
        """Trigger AI Market Price Sync (Elite V2.2: Price Intel)."""
        res_data = await product_service.sync_market_price(db_session, product_id)
        await db_session.commit()
        return SuccessResponse(message="Thành công", data=res_data)
