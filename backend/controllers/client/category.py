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

        from backend.database import current_tenant_id
        tid = current_tenant_id.get()
        
        stmt = select(Category).where(
            Category.slug == slug,
            Category.deleted_at == None,
            Category.tenant_id == tid
        )
        result = await db_session.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category with slug '{slug}' not found")

        # Elite V2.2: Generate SEO Meta with FAQs (GEO 2026 Strategy)
        from backend.services.commerce.seo_service import SeoService
        from backend.schemas.category import CategoryMetadata

        # Prepare FAQs for SEO Service
        faqs = []
        seo_keywords = None
        db_meta = category.category_metadata or {}
        if isinstance(db_meta, dict):
            if "faqs" in db_meta:
                faqs = db_meta["faqs"]
            if "seo_keywords" in db_meta:
                seo_keywords = db_meta["seo_keywords"]
        
        verified_metadata = CategoryMetadata.model_validate(db_meta) if db_meta else CategoryMetadata()

        await SeoService._resolve_settings(db_session)
        seo_meta = SeoService.generate_category_seo_meta(
            name=category.name,
            slug=category.slug,
            description=category.description,
            faqs=faqs,
            seo_title=category.seo_title,
            seo_description=category.seo_description,
            seo_keywords=seo_keywords,
        )

        return CategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            parent_id=str(category.parent_id) if category.parent_id else None,
            product_count=0, # Simplified for detail view
            children=[],
            description=category.description,
            seo_title=category.seo_title,
            seo_description=category.seo_description,
            image=category.image,
            icon=category.icon,
            position=category.position or 0,
            show_on_mobile=category.show_on_mobile if category.show_on_mobile is not None else True,
            show_on_desktop=category.show_on_desktop if category.show_on_desktop is not None else True,
            category_metadata=verified_metadata,
            seo_meta=seo_meta,
            created_at=category.created_at
        )
