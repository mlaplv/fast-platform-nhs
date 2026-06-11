"""
Elite V2.2 SEO Service — AI-Ready Semantic Synchronization.
Chuẩn hoá Metadata + Schema.org JSON-LD để tối ưu Google Rich Results
và AI Search engines (Gemini, Perplexity, ChatGPT, Claude).

GEO 2026 Strategy:
- Product + Offer + AggregateRating + Review + BreadcrumbList + FAQPage
- Organization + WebSite + SearchAction (Homepage)
- Article + BreadcrumbList (News)
- CollectionPage + ItemList + BreadcrumbList (Category)

Tuân thủ kỷ luật:
- Full-Async tĩnh (staticmethod), Zero-Hydration output (pre-serialized string)
- Cấm 'any' type, cấm hardcode ngoài config
- RAM safe: json.dumps(separators=...) loại bỏ whitespace thừa
"""
import json
import logging
import os
import re
from typing import Optional

from backend.schemas.product import ProductResponse, SeoMetaSchema
from backend.utils.schema_mutator import mutate_json_ld

logger = logging.getLogger("api-gateway")

# ── Config từ Env để tránh hardcode ────────────────────────────────────────────
_BASE_DOMAIN: str = os.getenv("APP_DOMAIN", "osmo")
_SITE_NAME: str = os.getenv("SEO_SITE_NAME", "osmo Elite")
_BRAND_NAME: str = os.getenv("SEO_BRAND_NAME", "osmo")
_SITE_URL: str = f"https://{_BASE_DOMAIN}"

# ── Layout: Google Title 50-60, Desc 150-160, ít nhất 8 từ khóa đuôi dài ─────
_TITLE_MAX = 60
_TITLE_TRIM = 57
_DESC_MAX = 160
_DESC_TRIM = 157

# ── Regex: Strip HTML tags ─────────────────────────────────────────────────────
_RE_HTML = re.compile(r'<[^>]+>')

# ── SGE Shield V1.0: In-process entropy cache — tránh async read trong sync context ──
_entropy_cfg_cache: dict[str, object] = {
    "enabled": True,
    "tone_override": None,
    "structure_override": None,
    "schema_drop_probability": 0.2,
    "lexical_sanitizer_enabled": True,
}


def update_entropy_cache(cfg: dict[str, object]) -> None:
    """SGE Shield: Update in-process cache khi Admin lưu settings. Called by SettingsService."""
    _entropy_cfg_cache.clear()
    _entropy_cfg_cache.update(cfg)
    logger.info("[SGE Shield] Entropy cache updated: enabled=%s", cfg.get("enabled"))


class SeoService:
    """
    Elite V2.2: Stateless SEO engine.
    Tạo metadata chất lượng cao cho cả Google & AI Search (Gemini/Perplexity/ChatGPT/Claude).
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE BUILDERS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        return _RE_HTML.sub('', text).strip()

    @staticmethod
    def _build_title(product: object, seo_title: Optional[str] = None) -> str:
        """Title ưu tiên trường admin nhập, fallback sang name + brand."""
        if isinstance(product, str):
            title = seo_title or f"{product} | {_BRAND_NAME}"
        else:
            name = getattr(product, "name", "Sản phẩm")
            title: str = seo_title or getattr(product, "seoTitle", None) or getattr(product, "seo_title", None) or f"{name} | {_BRAND_NAME}"
        
        # Tước bỏ HTML tags nếu có
        title = SeoService._strip_html(title)
        if len(title) > _TITLE_MAX:
            title = title[:_TITLE_TRIM] + "…"
        return title

    @staticmethod
    def _build_description(product: object) -> str:
        """
        Desc ưu tiên: seoDescription → shortDescription → description (cắt câu hoàn chỉnh).
        Hỗ trợ cả Pydantic model (camelCase) và SQLAlchemy model (snake_case).
        """
        seo_desc = getattr(product, "seoDescription", None) or getattr(product, "seo_description", None)
        short_desc = getattr(product, "shortDescription", None) or getattr(product, "short_description", None)
        full_desc = getattr(product, "description", None)
        
        raw: Optional[str] = seo_desc or short_desc or full_desc

        if not raw:
            name = getattr(product, "name", "sản phẩm")
            return f"Mua {name} chính hãng tại {_SITE_NAME}. Cam kết chất lượng, hỗ trợ 24/7."

        # Tước bỏ HTML tags nếu có (description có thể chứa HTML)
        raw = SeoService._strip_html(raw)

        if len(raw) <= _DESC_MAX:
            return raw

        # Cắt đến khoảng trắng gần nhất trước giới hạn để không bị đứt từ
        truncated: str = raw[:_DESC_TRIM]
        last_space: int = truncated.rfind(' ')
        if last_space > _DESC_TRIM - 20:  # Nếu khoảng trắng gần cuối thì cắt ở đó
            truncated = truncated[:last_space]
        return truncated + "…"

    @staticmethod
    def _build_keywords(product: object) -> str:
        """
        Keywords đuôi dài (long-tail) theo chuẩn 2026 Vietnam E-commerce SEO.
        Ưu tiên admin nhập; fallback tự sinh từ tên + category + brand.
        """
        seo_keywords = getattr(product, "seoKeywords", None) or getattr(product, "seo_keywords", None)
        if seo_keywords:
            return seo_keywords

        name: str = getattr(product, "name", "sản phẩm")
        cat: str = getattr(product, "category", "") or getattr(product, "category_name", "") or ""
        brand: str = _BRAND_NAME
        site: str = _SITE_NAME

        parts: list[str] = [
            name,
            f"{name} chính hãng",
            f"{name} giá rẻ",
            f"mua {name}",
            f"{name} {brand}",
            f"{name} review",
            f"thuốc {cat}" if cat else "",
            f"{cat} hiệu quả" if cat else "",
            brand,
            site,
        ]
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _build_json_ld(
        product: ProductResponse,
        canonical_url: str,
        desc: str,
    ) -> str:
        """
        Build Schema.org JSON-LD: Product + Offer + AggregateRating + Review.
        GEO 2026: @id anchoring, priceValidUntil, brand from metadata.
        """
        effective_price: float = (
            product.discountPrice if product.discountPrice else product.price
        )

        # Brand: ưu tiên metadata.brand → env fallback
        brand_name: str = _BRAND_NAME
        if product.metadata:
            meta_brand = getattr(product.metadata, "brand", None)
            if isinstance(meta_brand, str) and meta_brand.strip():
                brand_name = meta_brand.strip()

        product_id: str = f"{_SITE_URL}/{product.slug}#product"

        schema: dict = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "@id": product_id,
            "name": product.name,
            "description": desc,
            "image": product.images if product.images else [],
            "sku": product.sku or product.id,
            "url": canonical_url,
            "brand": {
                "@type": "Brand",
                "name": brand_name,
            },
            "offers": {
                "@type": "Offer",
                "@id": f"{canonical_url}#offer",
                "url": canonical_url,
                "priceCurrency": "VND",
                "price": effective_price,
                "priceValidUntil": "2026-12-31",
                "availability": (
                    "https://schema.org/InStock"
                    if product.stock > 0
                    else "https://schema.org/OutOfStock"
                ),
                "itemCondition": "https://schema.org/NewCondition",
                "seller": {
                    "@type": "Organization",
                    "name": _SITE_NAME,
                },
            },
        }

        # AggregateRating + Review từ metadata.reviews (tối đa 5 để không phình schema)
        meta_reviews: list = []
        if product.metadata:
            raw_reviews = getattr(product.metadata, "reviews", None)
            if isinstance(raw_reviews, list):
                meta_reviews = raw_reviews

        if meta_reviews:
            total_rating: float = 0.0
            count: int = 0
            review_nodes: list[dict] = []

            for r in meta_reviews:
                rating: float = float(r.get("rating", 5))
                total_rating += rating
                count += 1
                if len(review_nodes) < 5:
                    review_nodes.append({
                        "@type": "Review",
                        "reviewRating": {
                            "@type": "Rating",
                            "ratingValue": f"{rating:.1f}",
                            "bestRating": "5",
                            "worstRating": "1",
                        },
                        "author": {
                            "@type": "Person",
                            "name": r.get("name") or r.get("author_name") or "Khách hàng xác thực",
                        },
                        "reviewBody": r.get("content", ""),
                    })

            # Elite 2026: AI Customer Sentiment Summary (Review Schema)
            if product.metadata:
                pos_notes = getattr(product.metadata, "positive_notes", [])
                neg_notes = getattr(product.metadata, "negative_notes", [])
                ai_summary = getattr(product.metadata, "customer_sentiment_summary", "")

                if pos_notes or neg_notes or ai_summary:
                    ai_review = {
                        "@type": "Review",
                        "author": {
                            "@type": "Organization",
                            "name": _SITE_NAME,
                        },
                        "reviewRating": {
                            "@type": "Rating",
                            "ratingValue": f"{total_rating / max(1, count):.1f}" if count > 0 else "5.0",
                            "bestRating": "5",
                        },
                        "reviewBody": ai_summary or "Tổng hợp đánh giá khách hàng.",
                    }
                    if pos_notes:
                        ai_review["positiveNotes"] = {
                            "@type": "ItemList",
                            "itemListElement": [{"@type": "ListItem", "position": i+1, "name": note} for i, note in enumerate(pos_notes)]
                        }
                    if neg_notes:
                        ai_review["negativeNotes"] = {
                            "@type": "ItemList",
                            "itemListElement": [{"@type": "ListItem", "position": i+1, "name": note} for i, note in enumerate(neg_notes)]
                        }
                    # Đưa AI Summary lên top đầu review
                    review_nodes.insert(0, ai_review)

            if review_nodes:
                schema["review"] = review_nodes
            
            if count > 0:
                schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": f"{total_rating / count:.1f}",
                    "reviewCount": str(count),
                    "bestRating": "5",
                    "worstRating": "1",
                }

        # Minified JSON — loại bỏ whitespace để tiết kiệm DOM/RAM
        return json.dumps(schema, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _build_breadcrumb_ld(
        product: ProductResponse,
        canonical_url: str,
    ) -> str:
        """
        GEO 2026: BreadcrumbList JSON-LD.
        Home → Category → Product
        """
        items: list[dict] = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Trang chủ",
                "item": {"@id": _SITE_URL},
            }
        ]

        if product.category:
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": product.category,
                "item": {"@id": f"{_SITE_URL}/{product.slug.split('-')[0]}/"},
            })
            items.append({
                "@type": "ListItem",
                "position": 3,
                "name": product.name,
                "item": {"@id": canonical_url},
            })
        else:
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": product.name,
                "item": {"@id": canonical_url},
            })

        schema: dict = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items,
        }
        return json.dumps(schema, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _build_faq_ld(faqs: list[dict]) -> str:
        """
        GEO 2026: FAQPage JSON-LD from product FAQs.
        AI Search engines (Perplexity, ChatGPT) strongly prefer FAQ structured data.
        """
        if not faqs:
            return ""

        qa_entities: list[dict] = []
        for faq in faqs:
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            if question and answer:
                qa_entities.append({
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer,
                    },
                })

        if not qa_entities:
            return ""

        schema: dict = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": qa_entities,
        }
        return json.dumps(schema, separators=(",", ":"), ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def generate_seo_meta(product: ProductResponse) -> SeoMetaSchema:
        """
        Entry point: Tạo đầy đủ SEO metadata + JSON-LD cho một sản phẩm.
        Output là SeoMetaSchema (strict-typed), không trả về bất kỳ 'Any'.
        """
        canonical_url: str = f"{_SITE_URL}/{product.slug}"

        title: str = SeoService._build_title(product, getattr(product, "seoTitle", None) or getattr(product, "seo_title", None))
        desc: str = SeoService._build_description(product)
        keywords: str = SeoService._build_keywords(product)
        json_ld: str = SeoService._build_json_ld(product, canonical_url, desc)
        breadcrumb_ld: str = SeoService._build_breadcrumb_ld(product, canonical_url)

        # FAQ JSON-LD from product metadata FAQs
        faq_ld: str = ""
        if product.metadata:
            raw_faqs = getattr(product.metadata, "faqs", None)
            if isinstance(raw_faqs, list) and raw_faqs:
                faq_dicts: list[dict] = []
                for f in raw_faqs:
                    if hasattr(f, "model_dump"):
                        faq_dicts.append(f.model_dump())
                    elif isinstance(f, dict):
                        faq_dicts.append(f)
                faq_ld = SeoService._build_faq_ld(faq_dicts)

        logger.debug(
            "[SeoService] Generated SEO meta for slug=%s title_len=%d desc_len=%d",
            product.slug,
            len(title),
            len(desc),
        )

        return SeoMetaSchema(
            title=title,
            description=desc,
            keywords=keywords,
            canonical_url=canonical_url,
            json_ld_string=json_ld,
            breadcrumb_ld_string=breadcrumb_ld,
            faq_ld_string=faq_ld,
        )

    @staticmethod
    def generate_category_seo_meta(
        name: str, 
        slug: str, 
        description: Optional[str] = None, 
        items: Optional[list] = None,
        faqs: Optional[list[dict]] = None,
        seo_title: Optional[str] = None,
        seo_description: Optional[str] = None,
        seo_keywords: Optional[str] = None
    ) -> SeoMetaSchema:
        """Tạo SEO cho trang danh mục."""
        canonical_url = f"{_SITE_URL}/{slug}/"
        title = seo_title or SeoService._build_title(name)
        
        # Build standard description for category
        desc = seo_description or description or f"Khám phá danh mục {name} chính hãng tại {_SITE_NAME}. Cam kết chất lượng, hỗ trợ tận tâm."
        desc = SeoService._strip_html(desc)
        if len(desc) > _DESC_MAX:
            desc = desc[:_DESC_TRIM] + "…"

        # Build CollectionPage JSON-LD
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{canonical_url}#collection",
            "name": name,
            "url": canonical_url,
            "description": desc,
        }
        if items:
            schema["mainEntity"] = {
                "@type": "ItemList",
                "numberOfItems": len(items),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": item.get("name"),
                        "url": f"{_SITE_URL}/{item.get('slug')}"
                    } for i, item in enumerate(items[:10])
                ]
            }

        # Build Breadcrumb
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": {"@id": _SITE_URL}},
                {"@type": "ListItem", "position": 2, "name": name, "item": {"@id": canonical_url}}
            ]
        }

        # GEO 2026: FAQ JSON-LD
        faq_ld: str = ""
        if faqs:
            faq_ld = SeoService._build_faq_ld(faqs)

        return SeoMetaSchema(
            title=title,
            description=desc,
            keywords=seo_keywords or f"{name}, {name} chính hãng, {_SITE_NAME}, {_BRAND_NAME}",
            canonical_url=canonical_url,
            json_ld_string=json.dumps(schema, separators=(",", ":"), ensure_ascii=False),
            breadcrumb_ld_string=json.dumps(breadcrumb, separators=(",", ":"), ensure_ascii=False),
            faq_ld_string=faq_ld
        )

    @staticmethod
    def generate_article_seo_meta(
        title: str,
        slug: str,
        excerpt: Optional[str] = None,
        image: Optional[str] = None,
        author: str = "Admin",
        date_published: Optional[str] = None,
        faqs: Optional[list[dict]] = None,
        seo_title: Optional[str] = None,
        seo_description: Optional[str] = None,
        seo_keywords: Optional[str] = None,
    ) -> "ArticleSeoMeta":
        """GEO 2026: Tạo SEO + FAQPage JSON-LD cho trang bài viết."""
        from backend.schemas.article import ArticleSeoMeta

        canonical_url = f"{_SITE_URL}/{slug}.html"
        final_seo_title = seo_title or SeoService._build_title(title)
        
        # Elite V2.2: Prioritize DB-configured seo_description, fallback to excerpt
        desc = seo_description or excerpt or f"Đọc bài viết {title} để biết thêm thông tin chi tiết và hữu ích tại {_SITE_NAME}."
        desc = SeoService._strip_html(desc)
        if len(desc) > _DESC_MAX:
            desc = desc[:_DESC_TRIM] + "…"

        # Build Article JSON-LD
        schema: dict = {
            "@context": "https://schema.org",
            "@type": "Article",
            "@id": f"{canonical_url}#article",
            "headline": title,
            "description": desc,
            "image": [image] if image else [],
            "datePublished": date_published or "2026-01-01",
            "author": {"@type": "Person", "name": author},
            "publisher": {"@type": "Organization", "name": _SITE_NAME, "logo": {"@type": "ImageObject", "url": f"{_SITE_URL}/favicon.svg"}},
            "url": canonical_url,
            "inLanguage": "vi",
        }

        # SGE Shield V1.0: Mutate Article JSON-LD schema
        entropy_cfg = SeoService._get_entropy_config()
        if entropy_cfg.get("enabled", True):
            schema = mutate_json_ld(
                schema,
                seed=slug,
                enable_drop=True,
                drop_probability=entropy_cfg.get("schema_drop_probability", 0.2),
            )

        # Breadcrumb
        breadcrumb: dict = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": {"@id": _SITE_URL}},
                {"@type": "ListItem", "position": 2, "name": "Bài viết", "item": {"@id": f"{_SITE_URL}/bai-viet"}},
                {"@type": "ListItem", "position": 3, "name": title, "item": {"@id": canonical_url}}
            ]
        }

        # SGE Shield: Mutate Breadcrumb JSON-LD
        if entropy_cfg.get("enabled", True):
            breadcrumb = mutate_json_ld(breadcrumb, seed=f"{slug}:bc")

        # GEO 2026: FAQ JSON-LD from article metadata
        faq_ld: str = ""
        if faqs:
            faq_ld = SeoService._build_faq_ld(faqs)

        # Elite V2.2: Prioritize DB-configured seo_keywords, fallback to default keywords list
        final_keywords = seo_keywords or f"{title}, bài viết, {_SITE_NAME}"

        return ArticleSeoMeta(
            title=final_seo_title,
            description=desc,
            keywords=final_keywords,
            canonical_url=canonical_url,
            json_ld_string=json.dumps(schema, separators=(",", ":"), ensure_ascii=False),
            breadcrumb_ld_string=json.dumps(breadcrumb, separators=(",", ":"), ensure_ascii=False),
            faq_ld_string=faq_ld,
        )

    @staticmethod
    def _get_entropy_config() -> dict[str, object]:
        """
        SGE Shield V1.0: Đọc entropy config từ in-process cache.
        Cache được cập nhật realtime khi Admin lưu settings (zero async overhead).
        """
        return _entropy_cfg_cache

    @staticmethod
    def generate_home_seo_meta(
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[str] = None,
        site_name: Optional[str] = None
    ) -> SeoMetaSchema:
        """Tạo SEO cho trang chủ (Elite V2.2)."""
        name = site_name or _SITE_NAME
        
        # GEO 2026: Ưu tiên dữ liệu từ Admin cấu hình
        final_title = title or name
        final_desc = description or f"{name} - Hệ thống chuyên cung cấp sản phẩm chăm sóc sức khỏe chính hãng, chất lượng cao."
        final_keywords = keywords or f"{name}, thực phẩm chức năng, chăm sóc sức khỏe"
        
        canonical_url = _SITE_URL

        # WebSite + SearchAction (GEO 2026 AI Ready)
        website_schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{_SITE_URL}#website",
            "url": _SITE_URL,
            "name": name,
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint", "urlTemplate": f"{_SITE_URL}/products?q={{search_term_string}}"},
                "query-input": "required name=search_term_string"
            }
        }

        # Organization (Branding trust for AI Search)
        org_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{_SITE_URL}#organization",
            "name": name,
            "url": _SITE_URL,
            "logo": f"{_SITE_URL}/favicon.svg",
            "sameAs": [] # Add social links if available
        }

        return SeoMetaSchema(
            title=final_title,
            description=final_desc,
            keywords=final_keywords,
            canonical_url=canonical_url,
            json_ld_string=json.dumps(website_schema, separators=(",", ":"), ensure_ascii=False),
            breadcrumb_ld_string=json.dumps(org_schema, separators=(",", ":"), ensure_ascii=False)
        )
