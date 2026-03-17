import re
import time
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models.content import Article, ArticleEmbedding
from backend.database import current_tenant_id
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.utils.sql import escape_like
from backend.schemas.article import CreateArticleRequest, UpdateArticleRequest

logger = logging.getLogger("api-gateway")

class ContentService:
    """
    ULTRA-LEAN CONTENT SERVICE (ELITE V2.2)
    ---------------------------------------
    Centralizes all Article & Content logic.
    Directly uses SQLAlchemy 2.0 ORM for maximum performance.
    """

    @staticmethod
    def _generate_slug(title: str) -> str:
        """Helper to generate a URL-safe slug from Vietnamese title."""
        slug = re.sub(
            r'[^a-z0-9]+', '-',
            title.lower()
                .replace("đ", "d")
                .replace("ă", "a").replace("â", "a")
                .replace("ê", "e").replace("ô", "o")
                .replace("ơ", "o").replace("ư", "u")
        ).strip("-")
        return f"{slug}-{int(time.time())}"

    async def list_articles(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Union[Sequence[Dict[str, Union[str, int, None]]], int]]:
        """List articles with Redis-backed count caching and eager loading."""

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

        # 1. COUNT Optimization via Redis Cache
        cache_key = f"articles:count:status={status}:cat={category}:search={search}"
        total = None

        if xohi_memory._use_redis:
            try:
                cached_count = await xohi_memory.client.get(cache_key)
                if cached_count is not None:
                    total = int(cached_count)
            except Exception as e:
                logger.debug(f"[ContentService] Redis count fetch failed: {e}")

        if total is None:
            count_stmt = select(func.count(Article.id)).where(and_(*conditions))
            total = await session.scalar(count_stmt) or 0

            if xohi_memory._use_redis:
                try:
                    await xohi_memory.client.set(cache_key, str(total), ex=300) # 5-min TTL
                except Exception as e:
                    logger.debug(f"[ContentService] Redis count set failed: {e}")

        # 2. Paginated fetch
        stmt = select(Article).where(and_(*conditions)).options(
            selectinload(Article.author)
        ).limit(limit).offset(offset).order_by(Article.created_at.desc())

        result = await session.execute(stmt)
        articles: Sequence[Article] = result.scalars().all()

        data = [
            {
                "id": str(a.id),
                "title": a.title,
                "slug": a.slug,
                "excerpt": a.excerpt,
                "status": a.status.lower() if a.status else "draft",
                "category": a.category,
                "views": a.views,
                "author": a.author.name if a.author else "System",
                "authorId": str(a.author_id) if a.author_id else None,
                "createdAt": a.created_at.strftime("%Y-%m-%d") if a.created_at else "",
            }
            for a in articles
        ]
        return {"data": data, "total": total}

    async def get_article(self, session: AsyncSession, article_id: str) -> Article:
        """Fetch a single article. Raises error if not found."""
        stmt = select(Article).where(Article.id == article_id, Article.deleted_at == None)
        result = await session.execute(stmt)
        article = result.scalar_one_or_none()
        if not article:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Article {article_id} not found")
        return article

    async def create_article(self, session: AsyncSession, data: CreateArticleRequest) -> Article:
        """Create article and trigger embedding generation."""
        slug = data.slug or self._generate_slug(data.title)

        article = Article(
            id=str(uuid.uuid4()),
            title=data.title,
            slug=slug,
            excerpt=data.excerpt,
            content=data.content,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            status=data.status.upper(),
            category=data.category,
            author_id=data.authorId,
        )
        session.add(article)

        # Flush to get ID if needed, though we generate it
        await session.flush()

        # Upsert Embedding (Async)
        await self._upsert_embedding(session, article.id, data.title, data.content)

        await session.commit()
        return article

    async def update_article(self, session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> Article:
        """Update article fields and refresh embedding if content changed."""
        article = await self.get_article(session, article_id)

        fields_changed = False
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "status":
                setattr(article, key, value.upper())
            else:
                setattr(article, key, value)
            if key in ["title", "content"]:
                fields_changed = True

        if fields_changed:
            await self._upsert_embedding(session, article_id, article.title, article.content)

        await session.commit()
        return article

    async def delete_articles(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete articles."""
        stmt = update(Article).where(Article.id.in_(ids)).values(
            deleted_at=datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    async def publish_articles(self, session: AsyncSession, ids: List[str]) -> int:
        """Bulk publish articles."""
        stmt = update(Article).where(Article.id.in_(ids)).values(status="PUBLISHED")
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    async def _upsert_embedding(self, session: AsyncSession, article_id: str, title: str, content: Optional[str]) -> None:
        """Surgical pgvector embedding update."""
        try:
            encoder = get_shared_encoder()
            if not encoder:
                logger.warning("[ContentService] Shared encoder not ready, skipping embedding")
                return

            text_to_embed = f"{title}\n{content or ''}".strip()

            # Offload heavy embedding to thread pool
            loop = asyncio.get_running_loop()

            def _embed() -> List["np.ndarray"]:
                return list(encoder.embed([text_to_embed]))

            embeddings = await loop.run_in_executor(None, _embed)

            if not embeddings:
                return

            vector = embeddings[0].tolist()
            vector_str = "[" + ",".join(map(str, vector)) + "]"

            tenant = current_tenant_id.get() or "default"

            # Rule R1.5: Atomic Upsert via Raw SQL for pgvector compatibility
            sql = text("""
                INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at, tenant_id)
                VALUES (:id, :article_id, :vector::vector, NOW(), NOW(), :tenant_id)
                ON CONFLICT (article_id)
                DO UPDATE SET embedding = :vector::vector, updated_at = NOW();
            """)
            await session.execute(sql, {
                "id": str(uuid.uuid4()),
                "article_id": article_id,
                "vector": vector_str,
                "tenant_id": tenant
            })
        except Exception as e:
            logger.error(f"[ContentService] Embedding failed for {article_id}: {e}")

# Global Instance
content_service = ContentService()
