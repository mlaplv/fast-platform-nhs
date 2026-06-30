from __future__ import annotations
import logging
from typing import List, Optional
from litestar import Controller, get, Request, route
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.schemas.article import ArticleResponse, ArticleListResponse
from backend.services.article_service import ArticleService, provide_article_service
from backend.services.article_vector_service import ArticleVectorService, provide_article_vector_service
from backend.services.commerce.seo_service import SeoService

logger = logging.getLogger("api-gateway")

from litestar.connection import ASGIConnection

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
        search: Optional[str] = None,
        tag: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ArticleListResponse:
        """PUBLIC: List news articles with pagination."""
        return await article_service.list_articles(
            db_session=db_session, 
            limit=limit, 
            offset=offset, 
            status="PUBLISHED", 
            search=search, 
            tag=tag,
            category="Bài viết",
            cursor=cursor
        )

    @get("/search")
    async def search_news(
        self,
        db_session: AsyncSession,
        article_service: ArticleService,
        q: str,
        limit: int = 5
    ) -> List[ArticleResponse]:
        """PUBLIC: Semantic/Vector search for news articles."""
        return await article_service.search_semantic(
            db_session=db_session,
            query=q,
            limit=limit
        )

    @get("/{article_id:str}")
    async def get_news_detail(
        self,
        db_session: AsyncSession,
        article_service: ArticleService,
        article_id: str,
        request: Request
    ) -> ArticleResponse:
        """PUBLIC: Get a single news article by ID."""
        try:
            article = await article_service.get_article(db_session, article_id)
            if request.method == "GET":
                await article_service.increment_views(db_session, article.id)
            if article.content:
                from backend.services.xohi_memory import xohi_memory
                cache_key = f"news:content:{article.id}"
                cached_content = None
                try:
                    if xohi_memory._use_redis and xohi_memory.client:
                        cached_content = await xohi_memory.client.get(cache_key)
                except Exception as ce:
                    logger.warning(f"Failed to fetch cached news content: {ce}")

                if cached_content:
                    article.content = cached_content
                else:
                    article.content = SeoService.harden_external_links(article.content)
                    article.content = await SeoService.inject_contextual_links(db_session, article.id, article.content)
                    try:
                        if xohi_memory._use_redis and xohi_memory.client:
                            await xohi_memory.client.set(cache_key, article.content, ex=3600)
                    except Exception as ce:
                        logger.warning(f"Failed to cache news content: {ce}")
            if article.status != "PUBLISHED":
                user = request.scope.get("state", {}).get("user")
                is_admin = False
                if user:
                    roles = user.get("roles", [])
                    perms = user.get("perms", [])
                    if "SUPER_ADMIN" in roles or "ADMIN" in roles or "content:read" in perms:
                        is_admin = True
                if not is_admin:
                    raise NotFoundException(f"Article {article_id} is not published")
            # GEO 2026: Inject SEO meta with FAQ JSON-LD
            faq_dicts = [f.model_dump() for f in article.metadata.faqs] if article.metadata.faqs else []
            article.seoMeta = await SeoService.generate_article_seo_meta(
                title=article.title,
                slug=article.slug,
                excerpt=article.excerpt,
                image=article.featuredImage,
                author=article.author,
                date_published=article.createdAt.isoformat() if article.createdAt else None,
                date_modified=article.updatedAt.isoformat() if article.updatedAt else None,
                faqs=faq_dicts,
                how_to=article.metadata.how_to,
                content=article.content,
                seo_title=article.seoTitle,
                seo_description=article.seoDescription,
                seo_keywords=article.seoKeywords,
                db=db_session,
            )
            return article
        except NotFoundException:
            raise NotFoundException(f"Article {article_id} not found")

    @route("/slug/{slug:str}", http_method=["GET", "HEAD"])
    async def get_news_by_slug(
        self,
        db_session: AsyncSession,
        article_service: ArticleService,
        slug: str,
        request: Request
    ) -> ArticleResponse:
        """PUBLIC: Get a single news article by slug."""
        try:
            article = await article_service.get_article_by_slug(db_session, slug)
            if request.method == "GET":
                await article_service.increment_views(db_session, article.id)
            if article.content:
                from backend.services.xohi_memory import xohi_memory
                cache_key = f"news:content:{article.id}"
                cached_content = None
                try:
                    if xohi_memory._use_redis and xohi_memory.client:
                        cached_content = await xohi_memory.client.get(cache_key)
                except Exception as ce:
                    logger.warning(f"Failed to fetch cached news content: {ce}")

                if cached_content:
                    article.content = cached_content
                else:
                    article.content = SeoService.harden_external_links(article.content)
                    article.content = await SeoService.inject_contextual_links(db_session, article.id, article.content)
                    try:
                        if xohi_memory._use_redis and xohi_memory.client:
                            await xohi_memory.client.set(cache_key, article.content, ex=3600)
                    except Exception as ce:
                        logger.warning(f"Failed to cache news content: {ce}")
            if article.status != "PUBLISHED":
                user = request.scope.get("state", {}).get("user")
                is_admin = False
                if user:
                    roles = user.get("roles", [])
                    perms = user.get("perms", [])
                    if "SUPER_ADMIN" in roles or "ADMIN" in roles or "content:read" in perms:
                        is_admin = True
                if not is_admin:
                    raise NotFoundException(f"Article with slug '{slug}' is not published")
            # GEO 2026: Inject SEO meta with FAQ JSON-LD
            faq_dicts = [f.model_dump() for f in article.metadata.faqs] if article.metadata.faqs else []
            article.seoMeta = await SeoService.generate_article_seo_meta(
                title=article.title,
                slug=article.slug,
                excerpt=article.excerpt,
                image=article.featuredImage,
                author=article.author,
                date_published=article.createdAt.isoformat() if article.createdAt else None,
                date_modified=article.updatedAt.isoformat() if article.updatedAt else None,
                faqs=faq_dicts,
                how_to=article.metadata.how_to,
                content=article.content,
                seo_title=article.seoTitle,
                seo_description=article.seoDescription,
                seo_keywords=article.seoKeywords,
                db=db_session,
            )
            return article
        except NotFoundException:
            raise NotFoundException(f"Article with slug '{slug}' not found")

    @get("/{article_id:str}/contextual-links")
    async def get_article_contextual_links(
        self,
        db_session: AsyncSession,
        article_id: str,
    ) -> dict:
        """PUBLIC: Get approved/applied SEO contextual links for a given article."""
        from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
        from sqlalchemy import select
        from backend.database import current_tenant_id

        tenant_id = current_tenant_id.get() or "default"
        # Return both APPROVED and APPLIED contextual links
        stmt = select(SeoContextualLink).where(
            SeoContextualLink.source_article_id == article_id,
            SeoContextualLink.status.in_([SeoContextualLinkStatus.APPROVED, SeoContextualLinkStatus.APPLIED]),
            SeoContextualLink.tenant_id == tenant_id,
        )
        res = await db_session.execute(stmt)
        links = res.scalars().all()
        return {
            "links": [
                {
                    "id": l.id,
                    "target_node_id": l.target_node_id,
                    "target_url": l.target_url,
                    "original_sentence": l.original_sentence,
                    "anchor_text": l.anchor_text,
                    "matched_entity_type": l.matched_entity_type.value if hasattr(l.matched_entity_type, 'value') else l.matched_entity_type,
                    "matched_entity_name": l.matched_entity_name,
                    "link_rel": l.link_rel,
                    "link_title": l.link_title,
                    "link_target": l.link_target,
                    "sentence_index": l.sentence_index,
                    "status": l.status.value if hasattr(l.status, 'value') else l.status,
                }
                for l in links
            ]
        }
