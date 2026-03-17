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
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
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
    ) -> Dict[str, object]:
        """List articles with Redis-backed count caching and Scalar Projection (Zero-Hydration)."""

        conditions = ["deleted_at IS NULL"]
        params = {"limit": limit, "offset": offset}

        if status and status != "all":
            conditions.append("status = :status")
            params["status"] = status.upper()
        if category and category != "all":
            conditions.append("category = :category")
            params["category"] = category
        if search:
            conditions.append("(title ILIKE :search OR category ILIKE :search)")
            params["search"] = f"%{escape_like(search)}%"

        where_clause = " AND ".join(conditions)

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
            count_sql = text(f"SELECT COUNT(*) FROM articles WHERE {where_clause}")
            total = await session.scalar(count_sql, params) or 0

            if xohi_memory._use_redis:
                try:
                    await xohi_memory.client.set(cache_key, str(total), ex=300)
                except Exception as e:
                    logger.debug(f"[ContentService] Redis count set failed: {e}")

        # 2. Paginated fetch via Scalar Projection
        sql = text(f"""
            SELECT a.id, a.title, a.slug, a.excerpt, a.status, a.category, a.views, a.created_at, u.name as author_name, a.author_id
            FROM articles a
            LEFT JOIN users u ON a.author_id = u.id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(sql, params)
        rows = result.all()

        data = [
            {
                "id": str(r[0]),
                "title": r[1],
                "slug": r[2],
                "excerpt": r[3],
                "status": r[4].lower() if r[4] else "draft",
                "category": r[5],
                "views": r[6],
                "createdAt": r[7].strftime("%Y-%m-%d") if r[7] else "",
                "author": r[8] or "System",
                "authorId": str(r[9]) if r[9] else None,
            }
            for r in rows
        ]
        return {"data": data, "total": total}

    async def get_article(self, session: AsyncSession, article_id: str) -> Dict[str, object]:
        """Fetch a single article via Scalar Projection."""
        sql = text("""
            SELECT id, title, slug, excerpt, content, status, category, seo_title, seo_description, author_id, created_at
            FROM articles
            WHERE id = :id AND deleted_at IS NULL
        """)
        result = await session.execute(sql, {"id": article_id})
        r = result.first()
        if not r:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Article {article_id} not found")

        return {
            "id": str(r[0]),
            "title": r[1],
            "slug": r[2],
            "excerpt": r[3],
            "content": r[4],
            "status": r[5].lower() if r[5] else "draft",
            "category": r[6],
            "seo_title": r[7],
            "seo_description": r[8],
            "author_id": str(r[9]) if r[9] else None,
            "createdAt": r[10].isoformat() if r[10] else "",
        }

    async def create_article(self, session: AsyncSession, data: CreateArticleRequest) -> Dict[str, object]:
        """Create article and trigger embedding generation (Zero-Hydration)."""
        slug = data.slug or self._generate_slug(data.title)
        new_id = str(uuid.uuid4())
        tenant = current_tenant_id.get() or "default"

        await session.execute(
            text("""
                INSERT INTO articles (
                    id, title, slug, excerpt, content, seo_title, seo_description,
                    status, category, author_id, tenant_id, created_at, updated_at
                ) VALUES (
                    :id, :title, :slug, :excerpt, :content, :seo_title, :seo_description,
                    :status, :category, :author_id, :tenant_id, NOW(), NOW()
                )
            """),
            {
                "id": new_id,
                "title": data.title,
                "slug": slug,
                "excerpt": data.excerpt,
                "content": data.content,
                "seo_title": data.seo_title,
                "seo_description": data.seo_description,
                "status": data.status.upper(),
                "category": data.category,
                "author_id": data.authorId,
                "tenant_id": tenant
            }
        )

        # Upsert Embedding (Async)
        await self._upsert_embedding(session, new_id, data.title, data.content)

        await session.commit()
        return {
            "id": new_id,
            "title": data.title,
            "slug": slug,
            "status": data.status.lower()
        }

    async def update_article(self, session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> Dict[str, object]:
        """Update article fields via direct SQL and refresh embedding if content changed (Zero-Hydration)."""
        # 1. Fetch current to check existence and for embedding logic
        sql = text("SELECT title, content FROM articles WHERE id = :id AND deleted_at IS NULL")
        res = await session.execute(sql, {"id": article_id})
        current = res.first()
        if not current:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Article {article_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return {"id": article_id, "message": "No changes"}

        set_clauses = []
        params = {"id": article_id}
        fields_changed = False

        for key, value in update_data.items():
            db_col = key
            if key == "authorId": db_col = "author_id"

            set_clauses.append(f"{db_col} = :{key}")
            if key == "status":
                params[key] = value.upper()
            else:
                params[key] = value

            if key in ["title", "content"]:
                fields_changed = True

        set_clauses.append("updated_at = NOW()")
        update_sql = text(f"UPDATE articles SET {', '.join(set_clauses)} WHERE id = :id")
        await session.execute(update_sql, params)

        if fields_changed:
            # Refresh embedding with new values
            final_title = update_data.get("title", current[0])
            final_content = update_data.get("content", current[1])
            await self._upsert_embedding(session, article_id, final_title, final_content)

        await session.commit()

        # Fetch basic return info
        res_info = await session.execute(text("SELECT title, status FROM articles WHERE id = :id"), {"id": article_id})
        r = res_info.first()

        return {
            "id": article_id,
            "title": r[0] if r else "",
            "status": r[1].lower() if r and r[1] else "draft"
        }

    async def delete_articles(self, session: AsyncSession, ids: List[str]) -> int:
        """Soft delete articles via Raw SQL."""
        sql = text("UPDATE articles SET deleted_at = NOW() WHERE id = ANY(:ids)")
        result = await session.execute(sql, {"ids": ids})
        await session.commit()
        return result.rowcount

    async def publish_articles(self, session: AsyncSession, ids: List[str]) -> int:
        """Bulk publish articles via Raw SQL."""
        sql = text("UPDATE articles SET status = 'PUBLISHED', updated_at = NOW() WHERE id = ANY(:ids)")
        result = await session.execute(sql, {"ids": ids})
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
