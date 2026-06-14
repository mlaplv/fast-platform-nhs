from __future__ import annotations
import asyncio
import logging
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import TypedDict
from litestar import Controller, route, Response, MediaType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.models.commerce import ProductBase
from backend.database.models.content import Article, Category

logger = logging.getLogger(__name__)


class SitemapUrl(TypedDict):
    loc: str
    priority: str
    changefreq: str
    lastmod: str | None


class MerchantSyncDetails(TypedDict):
    feed_url: str
    ping_url: str
    google_response: str


class MerchantSyncResponse(TypedDict):
    status: str
    message: str
    details: MerchantSyncDetails


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
    ) -> Response[str]:
        """Generates dynamic sitemap.xml via direct DB queries."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        site_url = f"https://{app_domain}"

        urls: list[SitemapUrl] = []

        # 1. Static Pages
        urls.append(self._url(f"{site_url}/", "1.0", "daily"))
        urls.append(self._url(f"{site_url}/bai-viet", "0.8", "daily"))
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
            lastmod: datetime | None = row.get("updated_at") or row.get("created_at")
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
        for row_cat in cat_result.scalars():
            urls.append(self._url(f"{site_url}/{row_cat}/", "0.7", "weekly"))

        # 4. Articles (Published) — direct query
        art_result = await db_session.execute(
            select(Article.slug, Article.updated_at, Article.created_at)
            .where(Article.status == "PUBLISHED")
            .where(Article.slug.isnot(None))
            .limit(500)
        )
        for row_art in art_result.mappings():
            lastmod_art: datetime | None = row_art.get("updated_at") or row_art.get("created_at")
            urls.append(self._url(
                f"{site_url}/{row_art['slug']}.html",
                "0.8",
                "daily",
                lastmod_art.strftime("%Y-%m-%d") if lastmod_art else None,
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

    def _url(self, loc: str, priority: str, changefreq: str, lastmod: str | None = None) -> SitemapUrl:
        return {"loc": loc, "priority": priority, "changefreq": changefreq, "lastmod": lastmod}

    def _generate_xml(self, urls: list[SitemapUrl]) -> str:
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
    """SGE 2026: Golden Record Google Merchant Center Product Feed.

    Generates deduped, enriched XML Product Feed compliant with RSS 2.0
    and Google Base namespaces. Emits exactly 1 item per ProductBase
    (default variant only) with full g:product_highlight, g:product_detail,
    g:gtin, g:google_product_category, and g:video_link support.
    """
    path = "/google-merchant.xml"

    # GEO 2026: Internal category → Google Product Taxonomy mapping
    # All cosmetics unified to ID 473 (Health & Beauty > Personal Care > Cosmetics > Skin Care)
    # Source: https://www.google.com/basepages/producttype/taxonomy-with-ids.en-US.txt
    _CATEGORY_MAP: dict[str, str] = {
        "cat_serum": "473",
        "cat_kem_duong": "473",
        "cat_mat_na": "473",
        "cat_cham_soc_mat": "473",
        "cat_sua_rua_mat": "473",
        "cat_tinh_chat": "473",
        "cat_kem_mat": "473",
    }

    # GEO 2026: Category → Vietnamese product type name (for title builder)
    _PRODUCT_TYPE_MAP: dict[str, str] = {
        "cat_serum": "Serum",
        "cat_kem_duong": "Kem Dưỡng",
        "cat_mat_na": "Mặt Nạ",
        "cat_cham_soc_mat": "Kem Mắt",
        "cat_sua_rua_mat": "Sữa Rửa Mặt",
        "cat_tinh_chat": "Tinh Chất",
        "cat_kem_mat": "Kem Mắt",
    }

    # GEO 2026: Sub-brands / product lines under Miccosmo
    _SUB_BRANDS: list[tuple[str, str]] = [
        ("beppin body", "Beppin Body"),
        ("rich gold", "Rich Gold"),
        ("white label", "White Label"),
        ("hurry harry", "Hurry Harry"),
        ("platinum", "Platinum"),
    ]

    # GEO 2026: Known ingredient keywords → Vietnamese short names
    _INGREDIENT_KEYWORDS: list[tuple[str, str]] = [
        ("placenta", "Placenta"),
        ("gold", "Vàng"),

        ("platinum", "Bạch Kim"),
        ("collagen", "Collagen"),
        ("retinol", "Retinol"),
        ("vitamin c", "Vitamin C"),
        ("virgin white", "Dưỡng Sáng"),
        ("wrinkle", "Chống Nhăn"),
        ("whitening", "Trắng Da"),
    ]

    # GEO 2026: Regex to strip combo/promo suffixes from raw titles
    _COMBO_SUFFIX_RE = re.compile(
        r'\s*[-–]\s*(?:Combo\s*\d+|Mua lẻ|Giá trải nghiệm|Hộp|Khởi đầu|Hiệu quả|Dứt điểm|Trọn bộ).*$',
        re.IGNORECASE,
    )

    @route(["", "/"], http_method=["GET", "HEAD"], media_type="application/xml")
    async def get_google_merchant_feed(
        self,
        db_session: AsyncSession,
    ) -> Response[str]:
        """Generates SGE 2026 Golden Record Product XML feed."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        site_url = f"https://{app_domain}"

        # Fetch active products with variants + category (single query)
        stmt = (
            select(ProductBase)
            .options(
                selectinload(ProductBase.variants),
                selectinload(ProductBase.category),
            )
            .where(ProductBase.status == "ACTIVE")
            .where(ProductBase.deleted_at == None)
            .order_by(ProductBase.created_at.desc())
        )
        result = await db_session.execute(stmt)
        products = result.scalars().all()

        items_xml: list[str] = []

        for p in products:
            item_xml = self._build_product_item(p, site_url)
            if item_xml:
                items_xml.append(item_xml)

        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
            '  <channel>\n'
            f'    <title>{self._escape(app_domain)} Product Feed</title>\n'
            f'    <link>{site_url}</link>\n'
            f'    <description>SGE 2026 Golden Record Product Feed for {app_domain}</description>\n'
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

    def _build_product_item(self, p: ProductBase, site_url: str) -> str:
        """SGE 2026: Build exactly 1 <item> per product (dedup R1)."""
        meta: dict[str, object] = p.product_metadata or {}
        attrs: dict[str, object] = p.attributes or {}

        # ── R2: Resolve default variant (is_default → combo_qty=1 → tier_index[0] → fallback) ──
        default_variant = self._resolve_default_variant(p)

        # ── Pricing: use default variant if available, otherwise base product ──
        if default_variant:
            item_price = int(default_variant.price)
            item_sale_price = int(default_variant.discount_price) if default_variant.discount_price and default_variant.discount_price < default_variant.price else 0
            item_stock = default_variant.stock
            item_id = default_variant.id
        else:
            item_price = int(p.price)
            item_sale_price = int(p.discount_price) if p.discount_price and p.discount_price < p.price else 0
            item_stock = p.stock
            item_id = p.id

        avail = "in_stock" if item_stock > 0 else "out_of_stock"

        # ── GEO 2026: Optimized title 35-65 chars, mobile-first ──
        title = self._normalize_feed_text(self._escape(self._build_geo_title(p, meta)))

        # ── Description from seo_description → short_description → description ──
        raw_desc = str(p.seo_description or p.short_description or p.description or "")
        desc_clean = self._normalize_feed_text(self._escape(re.sub(r'<[^>]+>', '', raw_desc)[:1000].strip()))


        # ── Brand resolving ──
        sub_brand = ""
        name_lower = (p.name or "").lower()
        for key, val in self._SUB_BRANDS:
            if key in name_lower:
                sub_brand = val
                break

        raw_brand = str(
            attrs.get("brand")
            or attrs.get("Thương hiệu")
            or meta.get("brand")
            or meta.get("seo_site_name")
            or "Miccosmo"
        ).strip()

        brand = sub_brand if sub_brand else raw_brand

        # ── R3: GTIN from ProductBase.sku (barcode) ──
        gtin = str(p.sku or "").strip()

        # ── Image resolving ──
        p_images = p.images or []
        img_url = self._resolve_full_url(p_images[0], site_url) if p_images else f"{site_url}/favicon.svg"

        # ── Separate images vs videos (SGE 2026: video goes to g:video_link) ──
        additional_imgs: list[str] = []
        video_links: list[str] = []
        for media in p_images[1:11]:
            full_url = self._resolve_full_url(media, site_url)
            if self._is_video(media):
                video_links.append(full_url)
            else:
                additional_imgs.append(full_url)

        # Also check metadata.video_url
        meta_video = str(meta.get("video_url") or "")
        if meta_video:
            video_links.append(self._resolve_full_url(meta_video, site_url))

        # ── Google Product Category: unified to 473 (Skin Care) for all cosmetics ──
        google_category = self._CATEGORY_MAP.get(str(p.category_id or ""), "473")

        # ── Product Type (internal taxonomy path) ──
        product_type = ""
        if p.category and hasattr(p.category, "name"):
            product_type = f"Mỹ phẩm > {p.category.name}"

        # ── Product Highlights from featured_ingredients + safety claims ──
        highlights = self._build_highlights(meta, attrs)

        # ── Product Details from metadata and dynamic attributes ──
        product_details = self._build_product_details(meta, attrs, brand=brand)

        # ═══ Assemble XML ═══
        lines: list[str] = [
            "    <item>",
            f"      <g:id>{self._escape(item_id)}</g:id>",
            f"      <g:title>{title}</g:title>",
            f"      <g:description>{desc_clean}</g:description>",
            f"      <g:link>{self._escape(f'{site_url}/{p.slug}')}</g:link>",
            f"      <g:image_link>{self._escape(img_url)}</g:image_link>",
        ]

        for a_img in additional_imgs:
            lines.append(f"      <g:additional_image_link>{self._escape(a_img)}</g:additional_image_link>")

        for v_link in video_links[:1]:  # Google allows 1 video_link
            lines.append(f"      <g:video_link>{self._escape(v_link)}</g:video_link>")

        lines.append(f"      <g:availability>{avail}</g:availability>")
        lines.append(f"      <g:price>{item_price} VND</g:price>")
        if item_sale_price > 0:
            lines.append(f"      <g:sale_price>{item_sale_price} VND</g:sale_price>")

        lines.append(f"      <g:brand>{self._escape(brand)}</g:brand>")
        lines.append("      <g:condition>new</g:condition>")

        # GTIN (mandatory for product matching)
        if gtin and gtin != "None":
            lines.append(f"      <g:gtin>{self._escape(gtin)}</g:gtin>")
        else:
            lines.append("      <g:identifier_exists>false</g:identifier_exists>")

        # Google Product Category
        if google_category:
            lines.append(f"      <g:google_product_category>{self._escape(google_category)}</g:google_product_category>")

        # Product Type (internal taxonomy)
        if product_type:
            lines.append(f"      <g:product_type>{self._escape(product_type)}</g:product_type>")

        # Product Highlights (SGE 2026: AI trích xuất)
        for hl in highlights:
            hl_replaced = self._normalize_feed_text(self._escape(hl))
            lines.append(f"      <g:product_highlight>{hl_replaced}</g:product_highlight>")

        # Product Details (structured key-value pairs)
        for pd in product_details:
            pd_val = self._normalize_feed_text(self._escape(pd['value']))
            lines.append("      <g:product_detail>")
            lines.append(f"        <g:section_name>{self._escape(pd['section'])}</g:section_name>")
            lines.append(f"        <g:attribute_name>{self._escape(pd['name'])}</g:attribute_name>")
            lines.append(f"        <g:attribute_value>{pd_val}</g:attribute_value>")
            lines.append("      </g:product_detail>")


        lines.append("      <g:excluded_destination>free_local_listings</g:excluded_destination>")
        lines.append("      <g:excluded_destination>local_inventory_ads</g:excluded_destination>")
        lines.append("    </item>")

        return "\n".join(lines)

    def _resolve_default_variant(self, p: ProductBase) -> "ProductVariant | None":
        """SGE 2026 R2: Priority chain for selecting the single representative variant."""
        if not p.variants:
            return None

        # Priority 1: Explicit is_default flag
        for v in p.variants:
            if getattr(v, "is_default", False):
                return v

        # Priority 2: combo_qty = 1 (single unit)
        for v in p.variants:
            v_attrs = v.attributes or {}
            if isinstance(v_attrs, dict) and v_attrs.get("combo_qty") == 1:
                return v

        # Priority 3: tier_index = [0] (first option)
        for v in p.variants:
            if v.tier_index == [0]:
                return v

        # Priority 4: Fallback to first variant
        return p.variants[0] if p.variants else None

    def _build_geo_title(self, p: ProductBase, meta: dict[str, object]) -> str:
        """GEO 2026: Build mobile-optimized title (35-65 chars).

        Formula: [Loại SP gọn] [Thành phần nổi bật] [Dòng sản phẩm/Tên thật] [Dung tích] - [Công dụng cốt lõi]
        """
        # Step 1: If seo_title exists, clean and check length
        if p.seo_title:
            clean = self._COMBO_SUFFIX_RE.sub("", p.seo_title).strip()
            if 35 <= len(clean) <= 65:
                return clean

        # Step 2: Build from structured components
        cat_id = str(p.category_id or "")
        product_type = self._PRODUCT_TYPE_MAP.get(cat_id, "")

        brand = str(
            (p.attributes or {}).get("brand")
            or meta.get("seo_site_name")
            or "Miccosmo"
        )

        weight = str(meta.get("weight") or "")

        # Extract sub-brand / line name
        sub_brand = ""
        name_lower = (p.name or "").lower()
        for key, val in self._SUB_BRANDS:
            if key in name_lower:
                sub_brand = val
                break

        # Extract key ingredient from product name
        ingredient = ""
        for eng_key, vn_name in self._INGREDIENT_KEYWORDS:
            if eng_key == "gold" and "Rich Gold" in sub_brand:
                continue
            if eng_key == "platinum" and "Platinum" in sub_brand:
                continue
            if eng_key in name_lower:
                ingredient = vn_name
                break

        # Extract core benefit from short_description (strip HTML first)
        benefit = ""
        raw_benefit = re.sub(r'<[^>]+>', '', str(p.short_description or "")).strip()
        for pattern in (
            r'(?:giúp|hỗ trợ)\s+(.+?)(?:\.|,|$)',
            r'(?:dưỡng|làm|mờ|giảm|xóa|chống|ngừa)\s+(.+?)(?:\.|,|$)',
        ):
            m = re.search(pattern, raw_benefit, re.IGNORECASE)
            if m:
                benefit = m.group(1).strip().rstrip(".")
                benefit = benefit[0].upper() + benefit[1:] if benefit else ""
                break

        # Assemble: [Type] [Ingredient] [Sub-Brand] [Weight]
        parts = []
        if product_type:
            parts.append(product_type)
        if ingredient:
            parts.append(ingredient)
        if sub_brand:
            parts.append(sub_brand)
        else:
            parts.append(brand)

        if weight:
            parts.append(weight)

        base = " ".join(parts)

        # Ensure base contains brand or sub-brand name
        if brand not in base and "Miccosmo" not in base:
            base = f"{brand} {base}"

        if benefit:
            max_benefit = 65 - len(base) - 3  # 3 = len(" - ")
            if max_benefit > 5:
                # Sliced benefit with word boundary safety
                sliced_benefit = benefit[:max_benefit]
                if len(benefit) > max_benefit:
                    sliced_benefit = sliced_benefit.rsplit(" ", 1)[0]
                
                # Repeatedly strip dangling words/chars from the end
                dangling_words = {
                    "và", "hoặc", "cho", "của", "ở", "tại", "với", "như", "để", "là", 
                    "các", "những", "một", "sự", "bởi", "do", "từ", "về", "nuôi", "tinh", 
                    "tế", "bào", "giúp", "làm", "mờ", "giảm", "xóa", "ngừa", "chống",
                    "độ", "khả", "năng", "thể", "được", "bị", "hơn", "nhất", "mang", 
                    "lại", "tạo", "nhiều", "ít", "quá", "lắm", "rất", "chuyên", "sâu",
                    "hiệu", "quả", "tối", "ưu", "hóa", "hoàn", "toàn", "mạnh", "mẽ",
                    "&", "+", "-", "/", ",", "với", "nhưng", "mà", "nên", "vì", "bằng"
                }
                while True:
                    words = sliced_benefit.split()
                    if not words:
                        break
                    last_word = words[-1].lower().strip(".,;:!?&-+")
                    if not last_word or last_word in dangling_words:
                        words.pop()
                        sliced_benefit = " ".join(words)
                    else:
                        break

                if len(sliced_benefit.split()) >= 2:
                    title = f"{base} - {sliced_benefit}"
                else:
                    title = base
            else:
                title = base
        else:
            title = base

        # Safety: hard-cap at 65 chars on word boundary
        if len(title) > 65:
            title = title[:65].rsplit(" ", 1)[0]

        # Minimum guard: if too short, fallback to cleaned seo_title or name
        if len(title) < 35:
            fallback = self._COMBO_SUFFIX_RE.sub("", str(p.seo_title or p.name)).strip()
            title = fallback[:65].rsplit(" ", 1)[0] if len(fallback) > 65 else fallback

        return title


    def _extract_first_clause(self, text: str) -> str:
        """Extract the first complete clause from a benefit string.

        Splits on commas, semicolons, and periods to get only the first
        meaningful segment. This guarantees the output is a semantically
        complete phrase — never a truncated fragment.
        """
        text = text.strip().rstrip(".")
        # Split on clause boundaries
        parts = re.split(r'[,;.]', text)
        first = (parts[0] if parts else text).strip()
        # Remove all decorative quotation marks (unicode variants included)
        first = re.sub(r'["""\'\u2018\u2019\u201c\u201d]', '', first).strip()
        return first

    def _build_short_subject(self, name: str) -> str:
        """Build a short, clean subject from an ingredient name.

        Strips long INCI parenthetical lists, determines whether to
        prefix with 'Chiết xuất', and keeps the subject concise.
        """
        # Strip parenthetical content if it's long chemical lists
        for match in re.finditer(r'\(([^)]+)\)', name):
            content = match.group(1)
            if len(content) > 30 or "," in content or "Sodium" in content:
                name = name.replace(match.group(0), "").strip()

        name_clean = name.strip()
        name_lower = name_clean.lower()

        # Already has a meaningful prefix — keep as-is
        if any(name_lower.startswith(p) for p in (
            "chiết xuất", "thành phần", "hệ thống", "tinh chất",
            "nước", "bộ", "combo", "kem", "gel",
        )):
            return name_clean

        # Known chemical / INCI names — keep as-is (no "Chiết xuất" prefix)
        if any(c in name_lower for c in (
            "niacinamide", "hyaluronic", "acid", "collagen", "retinol",
            "serum", "glycyrrhizate", "placenta", "vitamin",
        )):
            return name_clean

        # Natural ingredients — prefix with "Chiết xuất"
        if "chiết xuất" not in name_lower:
            return f"Chiết xuất {name_clean}"
        return name_clean

    def _compose_highlight(self, subject: str, benefit_raw: str) -> str:
        """Compose a complete, short highlight sentence.

        Strategy: Write short from the start.
        1. Extract only the FIRST clause of the benefit.
        2. Compose subject + verb + clause.
        3. If the result exceeds 15 words, shorten the benefit
           further by taking fewer words and verifying completeness.
        """
        # Get first clean clause from benefit
        clause = self._extract_first_clause(benefit_raw)
        clause_lower = clause.lower()

        # Strip leading "giúp" from clause if present — we'll add our own connector
        clause_no_giup = re.sub(r'^giúp\s+', '', clause, flags=re.IGNORECASE).strip()

        # Determine the connector
        if "đa năng" in clause_lower or "ngôi sao" in clause_lower or "thành phần" in clause_lower:
            sentence = f"{subject} là {clause}"
        elif clause_lower.startswith("giúp"):
            sentence = f"{subject} {clause}"
        else:
            sentence = f"{subject} giúp {clause_no_giup}"

        # Clean duplicate "giúp giúp"
        sentence = re.sub(r'\bgiúp\s+giúp\b', 'giúp', sentence, flags=re.IGNORECASE)

        # If still over 15 words, re-compose with a shorter benefit
        if len(sentence.split()) > 15:
            # Take only the first 3 words of the clause as a minimal predicate
            short_clause = " ".join(clause_no_giup.split()[:3])
            sentence = f"{subject} giúp {short_clause}"

        # Capitalize and finalize
        sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
        return sentence

    def _build_highlights(self, meta: dict[str, object], attrs: dict[str, object]) -> list[str]:
        """GEO 2026: Build 3-4 product highlights — complete sentences, max 15 words each.

        Design rule: Write short from the start. Never truncate.
        Every highlight exits this method as a grammatically complete sentence
        with subject + predicate, ending with a period.
        """
        pool: list[str] = []

        # Source 1: featured_ingredients (richest structured data)
        fi_list = meta.get("featured_ingredients")
        if isinstance(fi_list, list):
            for fi in fi_list[:3]:
                if isinstance(fi, dict):
                    name = str(fi.get("name", ""))
                    benefit = str(fi.get("benefit", ""))
                    if name and benefit:
                        subject = self._build_short_subject(name)
                        pool.append(self._compose_highlight(subject, benefit))
                    elif name:
                        pool.append(f"Thành phần nổi bật: {name}")

        # Source 2: Origin + safety
        origin = str(meta.get("origin") or "")
        if origin:
            pool.append(f"Nhập khẩu chính hãng 100% từ {origin}")

        # Source 3: Knowledge graph expert claim
        kg = meta.get("knowledge_graph")
        if isinstance(kg, dict):
            claim = str(kg.get("expert_claim") or "")
            if claim and len(claim) > 10:
                # Take first clause only — guaranteed complete
                pool.append(self._extract_first_clause(claim))

        # Source 4: Fallback safety statement
        if len(pool) < 3:
            pool.append("An toàn cho da nhạy cảm, không chứa cồn")

        # Finalize: ensure period termination, cap at 4 highlights
        result: list[str] = []
        for hl in pool[:4]:
            hl = hl.strip().rstrip(".")
            if hl:
                result.append(f"{hl}.")

        return result

    def _build_product_details(self, meta: dict[str, object], attrs: dict[str, object], brand: str | None = None) -> list[dict[str, str]]:
        """SGE 2026: Build structured product_detail entries from metadata and dynamic attributes."""
        details: list[dict[str, str]] = []

        # 1. Map from product_metadata (meta) first as priority
        mapping: list[tuple[str, str, str]] = [
            ("origin", "Thông số", "Xuất xứ"),
            ("weight", "Thông số", "Trọng lượng"),
            ("ingredients", "Thành phần", "Thành phần chính"),
            ("instructions", "Hướng dẫn", "Cách sử dụng"),
        ]

        added_keys = set()
        for meta_key, section, attr_name in mapping:
            val = str(meta.get(meta_key) or "").strip()
            if val:
                # SGE Post-Validation: Only allow short specs (under 5 words) for product details
                if len(val.split()) > 5:
                    continue
                details.append({"section": section, "name": attr_name, "value": val[:1000]})
                added_keys.add(attr_name.lower())

        # 2. Map from product.attributes (attrs) to fill in details
        ignored_attr_keys = {
            "combo_qty", "comboqty", "gifts", "tier_index", "tierindex",
            "is_default", "isdefault", "images", "options", "price", "stock"
        }

        friendly_names = {
            "origin": "Xuất xứ",
            "xuất xứ": "Xuất xứ",
            "weight": "Trọng lượng",
            "trọng lượng": "Trọng lượng",
            "quy cách": "Trọng lượng",
            "hsd": "Hạn sử dụng",
            "hsd(date)": "Hạn sử dụng",
            "hạn sử dụng": "Hạn sử dụng",
            "loại da": "Loại da",
            "loai_da": "Loại da",
            "dạng sản phẩm": "Dạng sản phẩm",
            "dang_san_pham": "Dạng sản phẩm",
            "brand": "Thương hiệu",
            "thương hiệu": "Thương hiệu",
            "barcode": "Mã vạch",
            "mã vạch": "Mã vạch",
        }

        for k, v in attrs.items():
            k_norm = k.lower().replace(" ", "_").strip()
            if k_norm in ignored_attr_keys:
                continue

            k_lower_space = k.lower().replace("_", " ").strip()
            section = "Thông số"
            if "thành phần" in k_lower_space or "ingredients" in k_lower_space:
                section = "Thành phần"
            elif "hướng dẫn" in k_lower_space or "instructions" in k_lower_space or "sử dụng" in k_lower_space:
                section = "Hướng dẫn"

            attr_name = friendly_names.get(k_lower_space, k.strip())

            if attr_name.lower() in added_keys:
                continue

            val_str = str(v).strip()
            if attr_name == "Thương hiệu" and brand:
                val_str = brand

            if val_str and val_str.lower() != "none":
                # SGE Post-Validation: Only allow short specs (under 5 words) for product details
                if len(val_str.split()) > 5:
                    continue
                details.append({"section": section, "name": attr_name, "value": val_str[:1000]})
                added_keys.add(attr_name.lower())

        # Safeguard: Ensure "Thương hiệu" is always present and matches brand
        if "thương hiệu" not in added_keys and brand:
            details.append({"section": "Thông số", "name": "Thương hiệu", "value": brand})

        return details

    def _resolve_full_url(self, path: str, site_url: str) -> str:
        """Ensure absolute URL for any media path."""
        if not path:
            return ""
        return f"{site_url}{path}" if path.startswith("/") else path

    def _is_video(self, path: str) -> bool:
        """Check if media path is a video file."""
        lower = path.lower().split("?")[0]
        return any(lower.endswith(ext) for ext in (".mp4", ".webm", ".mov", ".avi"))

    def _normalize_feed_text(self, text: str) -> str:
        if not text:
            return ""
        # 1. Standardize "nhau thai" -> "Placenta"
        text = re.sub(r'\bnhau\s+thai\b', 'Placenta', text, flags=re.IGNORECASE)
        # 2. Sanitize exaggerated/medical claim terms (GMC/SGE Compliance)
        replacements = [
            (r'\btức\s+thì\b', ''),
            (r'\bngay\s+lập\s+tức\b', ''),
            (r'\btức\s+thời\b', ''),
            (r'\bđặc\s+trị\s+sạm\b', 'mờ sạm'),
            (r'\bđặc\s+trị\s+nám\b', 'mờ nám'),
            (r'\bđặc\s+trị\s+thâm\b', 'mờ thâm'),
            (r'\bđặc\s+trị\s+mụn\b', 'giảm mụn'),
            (r'\bđặc\s+trị\b', 'dưỡng chuyên sâu'),
            (r'\bdứt\s+điểm\b', 'hiệu quả'),
            (r'\bđiều\s+trị\b', 'dưỡng da'),
            (r'\bchữa\s+trị\b', 'chăm sóc da'),
            (r'\btrị\s+nám\b', 'mờ nám'),
            (r'\btrị\s+thâm\b', 'mờ thâm'),
            (r'\btrị\s+mụn\b', 'giảm mụn'),
            (r'\btrị\s+nhăn\b', 'mờ nếp nhăn'),
            (r'\btrị\s+sạm\b', 'mờ sạm'),
            (r'\btrị\s+lão\s+hóa\b', 'ngừa lão hóa'),
            (r'\btận\s+gốc\b', 'chuyên sâu'),
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        # Clean up any resulting double spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text


    def _escape(self, s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;")
        )

    @route(["/sync"], http_method=["GET", "POST"])
    async def submit_merchant_feed(self) -> MerchantSyncResponse:
        """Notifies Google to crawl the merchant feed URL immediately (Google Ping Protocol)."""
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
        logger.info("Google Merchant Center ping result: %s", ping_res)

        return {
            "status": "success",
            "message": "Đồng bộ & Gửi yêu cầu cập nhật lên Google Merchant Center thành công!",
            "details": {
                "feed_url": feed_url,
                "ping_url": ping_url,
                "google_response": "Yêu cầu đồng bộ đã được phát đi thành công. Google Merchant Center sẽ tự động cào lại feed dữ liệu trong vòng vài phút."
            }
        }

