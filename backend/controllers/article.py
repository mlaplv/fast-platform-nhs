import re
import time
import uuid
import logging
from datetime import datetime, timezone
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models.content import Article
from backend.services.content_service import content_service
from backend.guards import PermissionGuard
from backend.schemas.article import CreateArticleRequest, UpdateArticleRequest, BulkIdsRequest

logger = logging.getLogger("api-gateway")

class ArticleController(Controller):
    """R2: Class-based Litestar Controller for Article/News CRUD."""
    path = "/api/v1/articles"

    @get("/", guards=[PermissionGuard("content:read")])
    async def list_articles(
        self,
        db_session: AsyncSession,
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, object]:
        """List articles via ContentService."""
        return await content_service.list_articles(
            session=db_session,
            limit=limit,
            offset=offset,
            status=status,
            search=search,
            category=category
        )

    @get("/{article_id:str}", guards=[PermissionGuard("content:read")])
    async def get_article(self, db_session: AsyncSession, article_id: str) -> Dict[str, object]:
        """Get a single article via ContentService."""
        return await content_service.get_article(db_session, article_id)

    @post("/", guards=[PermissionGuard("content:write")])
    async def create_article(self, db_session: AsyncSession, data: CreateArticleRequest) -> Dict[str, object]:
        """Create a new article via ContentService."""
        return await content_service.create_article(db_session, data)

    @patch("/{article_id:str}", guards=[PermissionGuard("content:write")])
    async def update_article(self, db_session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> Dict[str, object]:
        """Update an article via ContentService."""
        return await content_service.update_article(db_session, article_id, data)

    @delete("/{article_id:str}", status_code=200, guards=[PermissionGuard("content:write")])
    async def delete_article(self, db_session: AsyncSession, article_id: str) -> dict:
        """Soft delete via ContentService."""
        await content_service.delete_articles(db_session, [article_id])
        return {"ok": True, "id": article_id}

    @post("/bulk-delete", guards=[PermissionGuard("content:write")])
    async def bulk_delete(self, db_session: AsyncSession, data: BulkIdsRequest) -> dict:
        """Bulk soft delete via ContentService."""
        count = await content_service.delete_articles(db_session, data.ids)
        return {"ok": True, "deleted": count}

    @post("/bulk-publish", guards=[PermissionGuard("content:publish")])
    async def bulk_publish(self, db_session: AsyncSession, data: BulkIdsRequest) -> dict:
        """Bulk publish via ContentService."""
        count = await content_service.publish_articles(db_session, data.ids)
        return {"ok": True, "published": count}

