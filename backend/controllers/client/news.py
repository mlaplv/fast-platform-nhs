from __future__ import annotations
import logging
from typing import List, Optional
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.schemas.article import ArticleResponse, ArticleListResponse
from backend.services.article_service import ArticleService, provide_article_service
from backend.services.article_vector_service import ArticleVectorService, provide_article_vector_service

logger = logging.getLogger("api-gateway")

class PublicNewsController(Controller):
    """Elite V2.2: Public News Controller for Client Storefront."""
    path = "/api/v1/client/news"
    dependencies = {
        "vector_service": Provide(provide_article_vector_service),
        "article_service": Provide(provide_article_service),
    }

    @get("/")
    async def list_news(
        self,
        db_session: AsyncSession,
        article_service: ArticleService,
        limit: int = 20,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ArticleListResponse:
        """PUBLIC: List news articles with pagination."""
        # Use status='PUBLISHED' to only show live news to clients
        return await article_service.list_articles(
            db_session=db_session, 
            limit=limit, 
            offset=offset, 
            status="PUBLISHED", 
            search=search, 
            category=category
        )

    @get("/{article_id:str}")
    async def get_news_detail(
        self,
        db_session: AsyncSession,
        article_service: ArticleService,
        article_id: str
    ) -> ArticleResponse:
        """PUBLIC: Get a single news article by ID."""
        try:
            article = await article_service.get_article(db_session, article_id)
            if article.status != "PUBLISHED":
                raise NotFoundException(f"Article {article_id} is not published")
            return article
        except NotFoundException:
            raise NotFoundException(f"Article {article_id} not found")
