import re
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import Article, User as UserModel
from backend.schemas.article import (
    ArticleResponse, ArticleListResponse, CreateArticleRequest,
    UpdateArticleRequest
)
from backend.schemas.common import SuccessResponse, BulkActionResponse
from backend.services.article_vector_service import article_vector_service
from backend.services.xohi_memory import xohi_memory
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class ArticleService:
    @staticmethod
    async def list_articles(
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ArticleListResponse:
        """List articles (R76: Scalar Projection). R1.5: Zero-Hydration."""
        conditions = [Article.deleted_at == None]
        if status and status != "all":
            conditions.append(Article.status == status.upper())
        if category and category != "all":
            conditions.append(Article.category == category)
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Article.title.ilike(f"%{safe}%"),
                Article.category.ilike(f"%{safe}%"),
            ))

        # 1. COUNT Cache Redis Optimization
        cache_key = f"articles:count:status={status}:cat={category}:search={search}"
        total = None

        if xohi_memory._use_redis:
            try:
                cached_count = await xohi_memory.client.get(cache_key)
                if cached_count is not None:
                    total = int(cached_count)
            except Exception:
                pass

        if total is None:
            count_stmt = select(func.count(Article.id)).where(and_(*conditions))
            total = await db_session.scalar(count_stmt) or 0

            if xohi_memory._use_redis:
                try:
                    await xohi_memory.client.set(cache_key, str(total), ex=300)
                except Exception:
                    pass

        # 2. Scalar Projection Fetch
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt,
            Article.status, Article.category, Article.views,
            Article.created_at, Article.author_id, Article.featured_image,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Article.created_at.desc())

        result = await db_session.execute(stmt)
        data = [ArticleResponse.model_validate(row._mapping) for row in result]
        return ArticleListResponse(data=data, total=total)

    @staticmethod
    async def get_article(db_session: AsyncSession, article_id: str) -> ArticleResponse:
        """Get a single article (R76: Scalar Projection)."""
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt, Article.content,
            Article.status, Article.category, Article.views,
            Article.seo_title, Article.seo_description, Article.featured_image,
            Article.created_at, Article.author_id,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            Article.id == article_id,
            Article.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Article {article_id} not found")

        return ArticleResponse.model_validate(row._mapping)

    @staticmethod
    async def create_article(db_session: AsyncSession, data: CreateArticleRequest) -> SuccessResponse:
        """Create a new article and its embedding."""
        slug = data.slug or re.sub(
            r'[^a-z0-9]+', '-',
            data.title.lower()
                .replace("đ", "d")
                .replace("ă", "a").replace("â", "a")
                .replace("ê", "e").replace("ô", "o")
                .replace("ơ", "o").replace("ư", "u")
        ).strip("-") + f"-{int(time.time())}"

        new_id = str(uuid.uuid4())
        article = Article(
            id=new_id,
            title=data.title,
            slug=slug,
            excerpt=data.excerpt,
            content=data.content,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            status=data.status.upper(),
            category=data.category,
            author_id=data.authorId,
            featured_image=data.featured_image,
        )
        db_session.add(article)

        # RAG Upsert
        await article_vector_service.upsert_article_embedding(
            db_session, new_id, data.title, data.content
        )

        return SuccessResponse(ok=True, id=new_id)

    @staticmethod
    async def update_article(db_session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> SuccessResponse:
        """Update an article and its embedding."""
        # Rule 1.5: Detail fetch for update (Surgical)
        stmt = select(Article).where(Article.id == article_id, Article.deleted_at == None)
        res = await db_session.execute(stmt)
        article = res.scalar_one_or_none()

        if not article:
            raise NotFoundException(f"Article {article_id} not found")

        if data.title is not None: article.title = data.title
        if data.slug is not None: article.slug = data.slug
        if data.excerpt is not None: article.excerpt = data.excerpt
        if data.content is not None: article.content = data.content
        if data.seo_title is not None: article.seo_title = data.seo_title
        if data.seo_description is not None: article.seo_description = data.seo_description
        if data.status is not None: article.status = data.status.upper()
        if data.category is not None: article.category = data.category
        if data.featured_image is not None: article.featured_image = data.featured_image

        if data.title is not None or data.content is not None:
            await article_vector_service.upsert_article_embedding(
                db_session, article_id, article.title, article.content
            )

        return SuccessResponse(ok=True, id=article_id)

    @staticmethod
    async def delete_article(db_session: AsyncSession, article_id: str) -> SuccessResponse:
        stmt = update(Article).where(Article.id == article_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=article_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(Article).where(Article.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def bulk_publish(db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(Article).where(Article.id.in_(ids)).values(status="PUBLISHED")
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

    @staticmethod
    async def bulk_patch(
        db_session: AsyncSession, ids: List[str], status: Optional[str] = None, category: Optional[str] = None
    ) -> BulkActionResponse:
        values = {}
        if status: values["status"] = status.upper()
        if category: values["category"] = category
        
        if not values:
            return BulkActionResponse(ok=True, count=0)
            
        stmt = update(Article).where(Article.id.in_(ids)).values(**values)
        await db_session.execute(stmt)
        return BulkActionResponse(ok=True, count=len(ids))

article_service = ArticleService()
