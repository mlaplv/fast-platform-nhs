from __future__ import annotations
import logging
from typing import List, Dict, Union, Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import ProductBaseRepository, provide_product_repo
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.product import CreateProductRequest, UpdateProductRequest, ProductResponse, ProductListResponse
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
    ) -> ProductListResponse:
        """List products (R76: Scalar Projection). R41: N+1 Safe."""
        return await product_service.list_products(db_session=db_session, limit=limit, offset=offset, status=status, search=search)

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

    @post("/seo-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)])
    async def suggest_seo(
        self,
        data: Dict[str, str]
    ) -> SuccessResponse:
        """
        AI Suggestion for SEO metadata.
        Payload expects: {"name": "...", "description": "..."}
        """
        # In a real app we'd inject ai_service properly, but here we can just mock or use the service if it exists.
        # Let's import pydantic_ai and trinity_bridge to generate content
        try:
            from pydantic_ai import Agent
            from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
            
            agent = Agent(
                system_prompt="You are an SEO Expert. Optimize SEO metadata for a product. Return ONLY concise valid JSON without markdown wrapping: {\"title\": \"...\", \"description\": \"...\", \"keywords\": \"...\"}"
            )
            prompt = f"Product Name: {data.get('name', '')}\nProduct Desc: {data.get('description', '')}"
            
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=30.0
            )
            
            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                import json
                import re
                match = re.search(r'\{.*\}', suggested_json_str, re.DOTALL)
                parsed = json.loads(match.group(0)) if match else {"title": "", "description": "", "keywords": ""}
                return SuccessResponse(message="Thành công", data=parsed)
            else:
                return SuccessResponse(message="AI không phản hồi", data={"title": f"{data.get('name')} Chính Hãng", "description": "Sản phẩm chính hãng", "keywords": ""})
                
        except Exception as e:
            return SuccessResponse(message=f"Lỗi kết nối AI: {str(e)}", data={"title": f"{data.get('name', '')} Chính Hãng", "description": "Mua sản phẩm chính hãng với nhiều ưu đãi", "keywords": ""})
