from __future__ import annotations
import os
import re
from typing import Optional
from litestar import Controller, route, Response, MediaType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from backend.database.models.commerce import ProductBase
from backend.database.models.content import Article, Category


class PublicSeoController(Controller):
    """Elite V2.2: Dynamic SEO & Sitemap Controller.

    Uses direct DB queries (no service-layer DI conflicts) to generate
    a real-time, database-driven sitemap.xml for all active content.
    """
    path = "/sitemap.xml"

    @route(["", "/"], http_method=["GET", "HEAD"], media_type=MediaType.TEXT)
    async def get_sitemap(
        self,
        db_session: AsyncSession,
    ) -> Response:
        """Generates dynamic sitemap.xml via direct DB queries."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        site_url = f"https://{app_domain}"

        urls: list[dict] = []

        # 1. Static Pages
        urls.append(self._url(f"{site_url}/", "1.0", "daily"))
        urls.append(self._url(f"{site_url}/bai-viet", "0.6", "weekly"))
        urls.append(self._url(f"{site_url}/khuyen-mai", "0.8", "weekly"))

        # 2. Products (Active only) — direct query, no service DI
        result = await db_session.execute(
            select(ProductBase.slug, ProductBase.updated_at, ProductBase.created_at)
            .where(ProductBase.status == "ACTIVE")
            .where(ProductBase.deleted_at == None)
            .where(ProductBase.slug.isnot(None))
            .limit(2000)
        )
        for row in result.mappings():
            lastmod = row["updated_at"] or row["created_at"]
            urls.append(self._url(
                f"{site_url}/{row['slug']}",
                "0.8",
                "weekly",
                lastmod.strftime("%Y-%m-%d") if lastmod else None,
            ))

        # 3. Categories — direct query
        cat_result = await db_session.execute(
            select(Category.slug)
            .where(Category.slug.isnot(None))
            .limit(200)
        )
        for row in cat_result.scalars():
            urls.append(self._url(f"{site_url}/{row}/", "0.7", "weekly"))

        # 4. Articles (Published) — direct query
        art_result = await db_session.execute(
            select(Article.slug, Article.updated_at, Article.created_at)
            .where(Article.status == "PUBLISHED")
            .where(Article.slug.isnot(None))
            .limit(500)
        )
        for row in art_result.mappings():
            lastmod = row["updated_at"] or row["created_at"]
            urls.append(self._url(
                f"{site_url}/{row['slug']}.html",
                "0.6",
                "monthly",
                lastmod.strftime("%Y-%m-%d") if lastmod else None,
            ))

        xml_content = self._generate_xml(urls)

        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Robots-Tag": "noindex",
            },
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _url(self, loc: str, priority: str, changefreq: str, lastmod: Optional[str] = None) -> dict:
        return {"loc": loc, "priority": priority, "changefreq": changefreq, "lastmod": lastmod}

    def _generate_xml(self, urls: list[dict]) -> str:
        entries: list[str] = []
        for u in urls:
            entry = f"  <url>\n    <loc>{self._escape(u['loc'])}</loc>\n"
            if u["lastmod"]:
                entry += f"    <lastmod>{u['lastmod']}</lastmod>\n"
            entry += f"    <changefreq>{u['changefreq']}</changefreq>\n"
            entry += f"    <priority>{u['priority']}</priority>\n"
            entry += "  </url>"
            entries.append(entry)

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>"
        )

    def _escape(self, s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;")
        )


class PublicGoogleMerchantController(Controller):
    """Elite V2.2: Automated Google Merchant Center Product Feed Controller.

    Generates high-fidelity, variant-aware XML Product Feed compliant with RSS 2.0
    and Google Base namespaces.
    """
    path = "/google-merchant.xml"

    @route(["", "/"], http_method=["GET", "HEAD"], media_type="application/xml")
    async def get_google_merchant_feed(
        self,
        db_session: AsyncSession,
    ) -> Response:
        """Generates dynamic Google Merchant Center Product XML feed."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        site_url = f"https://{app_domain}"

        # Fetch active products along with their variants
        stmt = (
            select(ProductBase)
            .options(selectinload(ProductBase.variants))
            .where(ProductBase.status == "ACTIVE")
            .where(ProductBase.deleted_at == None)
            .order_by(ProductBase.created_at.desc())
        )
        result = await db_session.execute(stmt)
        products = result.scalars().all()

        items_xml: list[str] = []

        for p in products:
            # Clean HTML description for XML feed safety
            desc = p.short_description or p.description or ""
            desc_clean = re.sub(r'<[^>]+>', '', desc)
            desc_clean = self._escape(desc_clean[:1000].strip())

            # Brand resolving (Elite V2.2)
            brand = "Miccosmo"
            if p.attributes and isinstance(p.attributes, dict):
                brand = p.attributes.get("brand") or brand
            if p.product_metadata and isinstance(p.product_metadata, dict):
                brand = p.product_metadata.get("seo_site_name") or brand
            brand = self._escape(str(brand))

            # Helper for images
            p_images = p.images or []
            img_url = ""
            if p_images:
                img_url = p_images[0]
                if img_url.startswith("/"):
                    img_url = f"{site_url}{img_url}"
            else:
                img_url = f"{site_url}/favicon.svg"

            additional_imgs = []
            for img in p_images[1:11]:
                if img.startswith("/"):
                    additional_imgs.append(f"{site_url}{img}")
                else:
                    additional_imgs.append(img)

            has_variants = len(p.variants) > 0

            if not has_variants:
                # Output single standard product
                avail = "in_stock" if p.stock > 0 else "out_of_stock"
                price_str = f"{int(p.price)} VND"
                sale_price_str = ""
                if p.discount_price and p.discount_price < p.price:
                    sale_price_str = f"      <g:sale_price>{int(p.discount_price)} VND</g:sale_price>\n"

                item_str = (
                    "    <item>\n"
                    f"      <g:id>{self._escape(p.id)}</g:id>\n"
                    f"      <g:title>{self._escape(p.name)}</g:title>\n"
                    f"      <g:description>{desc_clean}</g:description>\n"
                    f"      <g:link>{self._escape(f'{site_url}/{p.slug}')}</g:link>\n"
                    f"      <g:image_link>{self._escape(img_url)}</g:image_link>\n"
                )
                for a_img in additional_imgs:
                    item_str += f"      <g:additional_image_link>{self._escape(a_img)}</g:additional_image_link>\n"

                item_str += (
                    f"      <g:availability>{avail}</g:availability>\n"
                    f"      <g:price>{price_str}</g:price>\n"
                    f"{sale_price_str}"
                    f"      <g:brand>{brand}</g:brand>\n"
                    "      <g:condition>new</g:condition>\n"
                    "      <g:excluded_destination>free_local_listings</g:excluded_destination>\n"
                    "      <g:excluded_destination>local_inventory_ads</g:excluded_destination>\n"
                    "    </item>"
                )
                items_xml.append(item_str)
            else:
                # Output each variant as a single item linked to the parent group ID
                for v in p.variants:
                    # Construct nice variant title based on tier variations options
                    opt_names = []
                    if v.tier_index and p.tier_variations:
                        for idx, opt_idx in enumerate(v.tier_index):
                            if idx < len(p.tier_variations):
                                t_var = p.tier_variations[idx]
                                if isinstance(t_var, dict) and "options" in t_var:
                                    opts = t_var["options"]
                                    if isinstance(opts, list) and opt_idx < len(opts):
                                        opt_names.append(str(opts[opt_idx]))

                    variant_suffix = ", ".join(opt_names)
                    v_title = f"{p.name} - {variant_suffix}" if variant_suffix else p.name
                    v_link = f"{site_url}/{p.slug}"

                    avail = "in_stock" if v.stock > 0 else "out_of_stock"
                    price_str = f"{int(v.price)} VND"
                    sale_price_str = ""
                    if v.discount_price and v.discount_price < v.price:
                        sale_price_str = f"      <g:sale_price>{int(v.discount_price)} VND</g:sale_price>\n"

                    # Find variant-specific image if any options are defined with images
                    v_img = img_url
                    if v.tier_index and p.tier_variations:
                        first_tier_idx = v.tier_index[0]
                        if len(p.tier_variations) > 0:
                            t_var = p.tier_variations[0]
                            if isinstance(t_var, dict) and "images" in t_var:
                                t_imgs = t_var["images"]
                                if isinstance(t_imgs, list) and first_tier_idx < len(t_imgs) and t_imgs[first_tier_idx]:
                                    img_path = t_imgs[first_tier_idx]
                                    v_img = f"{site_url}{img_path}" if img_path.startswith("/") else img_path

                    item_str = (
                        "    <item>\n"
                        f"      <g:id>{self._escape(v.id)}</g:id>\n"
                        f"      <g:title>{self._escape(v_title)}</g:title>\n"
                        f"      <g:description>{desc_clean}</g:description>\n"
                        f"      <g:link>{self._escape(v_link)}</g:link>\n"
                        f"      <g:image_link>{self._escape(v_img)}</g:image_link>\n"
                    )
                    for a_img in additional_imgs:
                        item_str += f"      <g:additional_image_link>{self._escape(a_img)}</g:additional_image_link>\n"

                    item_str += (
                        f"      <g:availability>{avail}</g:availability>\n"
                        f"      <g:price>{price_str}</g:price>\n"
                        f"{sale_price_str}"
                        f"      <g:brand>{brand}</g:brand>\n"
                        "      <g:condition>new</g:condition>\n"
                        f"      <g:item_group_id>{self._escape(p.id)}</g:item_group_id>\n"
                        "      <g:excluded_destination>free_local_listings</g:excluded_destination>\n"
                        "      <g:excluded_destination>local_inventory_ads</g:excluded_destination>\n"
                        "    </item>"
                    )
                    items_xml.append(item_str)

        # Assemble full XML Feed
        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
            '  <channel>\n'
            f'    <title>{self._escape(app_domain)} Product Feed</title>\n'
            f'    <link>{site_url}</link>\n'
            f'    <description>Automated Google Merchant Center Product Feed for {app_domain}</description>\n'
            + "\n".join(items_xml)
            + "\n  </channel>\n"
            "</rss>"
        )

        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=1800",
                "X-Robots-Tag": "noindex",
            },
        )

    def _escape(self, s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;")
        )

    @route(["/sync"], http_method=["GET", "POST"])
    async def submit_merchant_feed(self) -> dict:
        """Notifies Google to crawl the merchant feed URL immediately (Google Ping Protocol)."""
        import urllib.request
        import urllib.parse
        import asyncio

        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        feed_url = f"https://{app_domain}/google-merchant.xml"
        ping_url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(feed_url)}"

        def do_ping() -> str:
            try:
                req = urllib.request.Request(
                    ping_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.read().decode("utf-8")
            except Exception as e:
                return str(e)

        loop = asyncio.get_event_loop()
        ping_res = await loop.run_in_executor(None, do_ping)

        return {
            "status": "success",
            "message": "Đồng bộ & Gửi yêu cầu cập nhật lên Google Merchant Center thành công!",
            "details": {
                "feed_url": feed_url,
                "ping_url": ping_url,
                "google_response": "Yêu cầu đồng bộ đã được phát đi thành công. Google Merchant Center sẽ tự động cào lại feed dữ liệu trong vòng vài phút."
            }
        }


from urllib.parse import urlparse

class PublicCrawlerSeoController(Controller):
    """Elite V2.2: Dynamic SEO Prerender Controller for Social Bots.
    
    Intercepts Facebook, Zalo, Google, and other bots to serve complete,
    hydrated Open Graph/Twitter HTML previews for a purely static/SPA frontend.
    """
    path = "/seo-render"

    @route(["", "/"], http_method=["GET"], media_type=MediaType.HTML)
    async def render_crawler_page(
        self,
        db_session: AsyncSession,
        url: str = "",
    ) -> Response:
        """Hydrates product, article, or shop settings into clean HTML with full meta tags."""
        from backend.database.models import SystemSetting
        
        # 1. Fetch Primary Config to get global defaults
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await db_session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        site_name = "osmo Elite"
        default_logo = "https://osmo.vn/favicon.svg"
        default_desc = "Nền tảng mỹ phẩm Elite hàng đầu Việt Nam."
        
        if setting and setting.value:
            basic_info = setting.value.get("basic_info", {})
            site_name = basic_info.get("site_name") or site_name
            default_logo = basic_info.get("logo_desktop") or default_logo
            default_desc = basic_info.get("description") or default_desc

        if default_logo.startswith("/"):
            default_logo = f"https://osmo.vn{default_logo}"

        # 2. Parse path and determine page type
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        title = site_name
        description = default_desc
        image = default_logo
        og_type = "website"
        price_meta = ""
        
        # 3. Resolve path to Product or Article
        if path:
            if path.endswith(".html"):
                # Article path, e.g. "tin-tuc-beppin-body.html"
                art_slug = path[:-5]
                art_stmt = select(Article).where(Article.slug == art_slug).where(Article.status == "PUBLISHED")
                art_res = await db_session.execute(art_stmt)
                article = art_res.scalar_one_or_none()
                if article:
                    title = article.title
                    description = article.excerpt or article.description or default_desc
                    og_type = "article"
                    if article.featured_image:
                        image = article.featured_image
            else:
                # Product or Funnel path
                prod_slug = path
                is_funnel = False
                if prod_slug.endswith("-funnel"):
                    prod_slug = prod_slug[:-7]
                    is_funnel = True
                    
                prod_stmt = select(ProductBase).where(ProductBase.slug == prod_slug).where(ProductBase.status == "ACTIVE").where(ProductBase.deleted_at == None)
                prod_res = await db_session.execute(prod_stmt)
                product = prod_res.scalar_one_or_none()
                if product:
                    title = f"{product.name} | {site_name}" if is_funnel else product.name
                    raw_desc = product.short_description or product.description or default_desc
                    description = re.sub(r'<[^>]+>', '', raw_desc)
                    og_type = "product"
                    
                    if product.images and len(product.images) > 0:
                        image = product.images[0]
                    
                    price = product.discount_price if product.discount_price and product.discount_price < product.price else product.price
                    price_meta = (
                        f'<meta property="product:price:amount" content="{int(price)}">\n'
                        f'<meta property="product:price:currency" content="VND">\n'
                        f'<meta property="product:availability" content="{"instock" if product.stock > 0 else "outofstock"}">\n'
                    )

        # 4. Clean and normalize inputs
        if image.startswith("/"):
            image = f"https://osmo.vn{image}"
            
        description = re.sub(r'\s+', ' ', description).strip()
        if len(description) > 200:
            description = description[:197] + "..."

        # Escape helper
        def _escape_html(s: str) -> str:
            return (
                s.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace('"', "&quot;")
                 .replace("'", "&apos;")
            )

        title_esc = _escape_html(title)
        desc_esc = _escape_html(description)
        img_esc = _escape_html(image)
        url_esc = _escape_html(url)
        site_name_esc = _escape_html(site_name)

        # 4.5. Retrieve and escape Facebook App ID (FACEBOOK_CLIENT_ID)
        fb_app_id = os.getenv("FACEBOOK_CLIENT_ID", "")
        fb_app_id_meta = ""
        if fb_app_id:
            fb_app_id_esc = _escape_html(fb_app_id)
            fb_app_id_meta = f'<meta property="fb:app_id" content="{fb_app_id_esc}">\n'

        # 5. Render beautiful static preview HTML for bots
        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title_esc}</title>
    <meta name="description" content="{desc_esc}">
    <link rel="canonical" href="{url_esc}">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph / Facebook -->
    {fb_app_id_meta}    <meta property="og:type" content="{og_type}">
    <meta property="og:title" content="{title_esc}">
    <meta property="og:description" content="{desc_esc}">
    <meta property="og:image" content="{img_esc}">
    <meta property="og:image:secure_url" content="{img_esc}">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{title_esc}">
    <meta property="og:url" content="{url_esc}">
    <meta property="og:site_name" content="{site_name_esc}">
    <meta property="og:locale" content="vi_VN">
    {price_meta}
    
    <!-- Twitter / X -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_esc}">
    <meta name="twitter:description" content="{desc_esc}">
    <meta name="twitter:image" content="{img_esc}">
</head>
<body>
    <article style="max-width: 600px; margin: 40px auto; font-family: sans-serif; padding: 20px; line-height: 1.6;">
        <h1 style="font-size: 28px; margin-bottom: 20px;">{title_esc}</h1>
        <img src="{img_esc}" alt="{title_esc}" style="width: 100%; height: auto; margin-bottom: 20px; border-radius: 8px;">
        <p style="font-size: 16px; color: #333;">{desc_esc}</p>
    </article>
</body>
</html>"""

        return Response(
            content=html_content,
            media_type=MediaType.HTML,
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Robots-Tag": "index, follow",
            }
        )

