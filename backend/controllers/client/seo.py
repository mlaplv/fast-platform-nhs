from __future__ import annotations
import os
from datetime import datetime
from typing import List
from litestar import Controller, get, Response, MediaType
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.commerce.product import ProductService, provide_product_service
from backend.services.commerce.category import CategoryService, provide_category_service
from backend.services.article_service import ArticleService, provide_article_service

class PublicSeoController(Controller):
    """Elite V2.2: Dynamic SEO & Sitemap Controller.
    
    This controller replaces the static frontend sitemap by providing
    real-time, database-driven XML content.
    """
    path = "/sitemap.xml"
    dependencies = {
        "product_service": Provide(provide_product_service),
        "category_service": Provide(provide_category_service),
        "article_service": Provide(provide_article_service),
    }

    @get("/", media_type=MediaType.TEXT)
    async def get_sitemap(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        category_service: CategoryService,
        article_service: ArticleService,
    ) -> Response:
        """Generates dynamic sitemap.xml."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        site_url = f"https://{app_domain}"
        
        urls = []
        
        # 1. Static Pages
        urls.append(self._build_url(f"{site_url}/home", "1.0", "daily"))
        urls.append(self._build_url(f"{site_url}/products", "0.8", "daily"))
        urls.append(self._build_url(f"{site_url}/bai-viet", "0.6", "weekly"))

        # 2. Products (Active only)
        products = await product_service.list_products(db_session, limit=1000, status="ACTIVE")
        for p in products.data:
            if p.slug:
                lastmod = p.updated_at or p.created_at
                urls.append(self._build_url(
                    f"{site_url}/{p.slug}", 
                    "0.8", 
                    "weekly", 
                    lastmod.strftime("%Y-%m-%d") if lastmod else None
                ))

        # 3. Categories
        categories = await category_service.list_categories(db_session)
        for cat in categories:
            if cat.slug:
                urls.append(self._build_url(f"{site_url}/{cat.slug}/", "0.7", "weekly"))

        # 4. Articles
        articles = await article_service.list_articles(db_session, limit=500)
        for art in articles:
            if art.slug:
                lastmod = art.updated_at or art.created_at
                urls.append(self._build_url(
                    f"{site_url}/{art.slug}", 
                    "0.6", 
                    "monthly",
                    lastmod.strftime("%Y-%m-%d") if lastmod else None
                ))

        xml_content = self._generate_xml(urls)
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Robots-Tag": "noindex" # Prevent sitemap itself from being indexed as a page
            }
        )

    def _build_url(self, loc: str, priority: str, changefreq: str, lastmod: str = None) -> dict:
        return {
            "loc": loc,
            "priority": priority,
            "changefreq": changefreq,
            "lastmod": lastmod
        }

    def _generate_xml(self, urls: List[dict]) -> str:
        entries = []
        for u in urls:
            entry = f"  <url>\n    <loc>{self._escape(u['loc'])}</loc>\n"
            if u['lastmod']:
                entry += f"    <lastmod>{u['lastmod']}</lastmod>\n"
            entry += f"    <changefreq>{u['changefreq']}</changefreq>\n"
            entry += f"    <priority>{u['priority']}</priority>\n"
            entry += "  </url>"
            entries.append(entry)
            
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"\n".join(entries)}
</urlset>"""

    def _escape(self, s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")
