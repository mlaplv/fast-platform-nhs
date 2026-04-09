from __future__ import annotations
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.schemas.category import CategoryResponse
from backend.services.commerce.category import CategoryService, provide_category_service
from litestar.exceptions import NotFoundException
from sqlalchemy import select
from backend.database.models import Category

class PublicCategoryController(Controller):
    """Elite V2.2: Public Category Controller for Client Funnels."""
    path = "/api/v1/client/categories"
    dependencies = {
        "category_service": Provide(provide_category_service),
    }

    @get("/slug/{slug:str}")
    async def get_category_by_slug(
        self,
        db_session: AsyncSession,
        category_service: CategoryService,
        slug: str
    ) -> CategoryResponse:
        """PUBLIC: Get a single category by slug."""
        # Normalize slug
        slug = slug.rstrip('/')

        stmt = select(Category).where(
            Category.slug == slug,
            Category.deleted_at == None
        )
        result = await db_session.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category with slug '{slug}' not found")

        # Reuse CategoryService structure if needed or map directly
        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            parent_id=category.parent_id,
            product_count=0, # Can be expanded to fetch real count
            children=[],
            description=category.description,
            seo_title=category.seo_title,
            seo_description=category.seo_description,
            image=category.image,
            icon=category.icon,
            created_at=category.created_at
        )
