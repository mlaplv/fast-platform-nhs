from __future__ import annotations
import logging
from typing import List, Dict, Union, Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import ArticleRepository, provide_article_repo
from backend.database.models import Article
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.schemas.article import (
    ArticleResponse, ArticleListResponse, CreateArticleRequest,
    UpdateArticleRequest, BulkPatchRequest
)
from backend.services.article_service import ArticleService, provide_article_service
from backend.services.article_vector_service import ArticleVectorService, provide_article_vector_service

logger = logging.getLogger("api-gateway")

class ArticleController(Controller):
    """R2: Class-based Litestar Controller for Article/News CRUD."""
    path = "/api/v1/articles"
    guards = [PermissionGuard(PermissionEnum.CONTENT_READ)]
    dependencies = {
        "art_repo": Provide(provide_article_repo),
        "vector_service": Provide(provide_article_vector_service),
        "article_service": Provide(provide_article_service),
    }
    
    @get("/categories", guards=[PermissionGuard(PermissionEnum.CONTENT_READ)])
    async def list_categories(self) -> List[str]:
        """Returns valid values from CategoryEnum for the UI. R1.5: Zero-Hydration."""
        from backend.services.xohi.creative_studio.models.schemas import CategoryEnum
        return [c.value for c in CategoryEnum]

    @get("/", guards=[PermissionGuard(PermissionEnum.CONTENT_READ)])
    async def list_articles(
        self, 
        db_session: AsyncSession,
        article_service: ArticleService,
        limit: int = 20, 
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ArticleListResponse:
        """List articles with server-side pagination. R41: N+1 Safe. R1.5: Zero-Hydration."""
        return await article_service.list_articles(db_session=db_session, limit=limit, offset=offset, status=status, search=search, category=category)

    @get("/{article_id:str}", guards=[PermissionGuard(PermissionEnum.CONTENT_READ)])
    async def get_article(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        article_id: str
    ) -> ArticleResponse:
        """Get a single article (R76: Scalar Projection)."""
        return await article_service.get_article(db_session, article_id)

    @post("/", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def create_article(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        data: CreateArticleRequest
    ) -> SuccessResponse:
        """Create a new article (Service-Centric RAG)."""
        res = await article_service.create_article(db_session, data)
        await db_session.commit()
        return res

    @patch("/{article_id:str}", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def update_article(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        article_id: str, 
        data: UpdateArticleRequest
    ) -> SuccessResponse:
        """Update an article (Service-Centric RAG)."""
        res = await article_service.update_article(db_session, article_id, data)
        await db_session.commit()
        return res

    @delete("/{article_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def delete_article(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        article_id: str
    ) -> SuccessResponse:
        """R18: Soft delete."""
        res = await article_service.delete_article(db_session, article_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def bulk_delete(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        data: BulkIdsRequest
    ) -> BulkActionResponse:
        """R18: Soft delete multiple articles."""
        res = await article_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-publish", guards=[PermissionGuard(PermissionEnum.CONTENT_PUBLISH)])
    async def bulk_publish(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        data: BulkIdsRequest
    ) -> BulkActionResponse:
        """Publish multiple articles."""
        res = await article_service.bulk_publish(db_session, data.ids)
        await db_session.commit()
        return res

    @patch("/bulk-update", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def bulk_patch(
        self, 
        db_session: AsyncSession, 
        article_service: ArticleService,
        data: BulkPatchRequest
    ) -> BulkActionResponse:
        """Bulk update status or category."""
        res = await article_service.bulk_patch(db_session, data.ids, data.status, data.category)
        await db_session.commit()
        return res

    @post("/faq-suggest", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
    async def suggest_faqs(
        self,
        article_service: ArticleService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto FAQ Generator for Articles."""
        title = data.get("title", "")
        content = data.get("content", "")
        faqs = await article_service.suggest_faqs(title, content)
        return {"data": faqs}

    @post("/seo-suggest", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
    async def suggest_seo(
        self,
        article_service: ArticleService,
        data: Dict[str, str],
    ) -> Dict[str, object]:
        """GEO 2026: XOHI Auto SEO Generator for Articles."""
        title = data.get("title", "")
        content = data.get("content", "")
        seo = await article_service.suggest_seo(title, content)
        return {"data": seo}
