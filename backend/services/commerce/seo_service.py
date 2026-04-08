"""
Elite V2.2 SEO Service — AI-Ready Semantic Synchronization.
Chuẩn hoá Metadata + Schema.org JSON-LD để tối ưu Google Rich Results
và AI Search engines (Gemini, Perplexity).

Tuân thủ kỷ luật:
- Full-Async tĩnh (staticmethod), Zero-Hydration output (pre-serialized string)
- Cấm 'any' type, cấm hardcode ngoài config
- RAM safe: json.dumps(separators=...) loại bỏ whitespace thừa
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from backend.schemas.product import ProductResponse, SeoMetaSchema

logger = logging.getLogger("api-gateway")

# ── Config từ Env để tránh hardcode ────────────────────────────────────────────
_BASE_DOMAIN: str = os.getenv("APP_DOMAIN", "micsmo.com")
_SITE_NAME: str = os.getenv("SEO_SITE_NAME", "Nhà Thuốc Hồng Sơn")
_BRAND_NAME: str = os.getenv("SEO_BRAND_NAME", "Hồng Sơn")

# ── Layout: Google Title 50-60, Desc 150-160, ít nhất 8 từ khóa đuôi dài ─────
_TITLE_MAX = 60
_TITLE_TRIM = 57
_DESC_MAX = 160
_DESC_TRIM = 157


class SeoService:
    """
    Elite V2.2: Stateless SEO engine.
    Tạo metadata chất lượng cao cho cả Google & AI Search (Gemini/Perplexity).
    """

    @staticmethod
    def _build_title(product: ProductResponse) -> str:
        """Title ưu tiên trường admin nhập, fallback sang name + brand."""
        title: str = product.seoTitle or f"{product.name} | {_BRAND_NAME}"
        if len(title) > _TITLE_MAX:
            title = title[:_TITLE_TRIM] + "…"
        return title

    @staticmethod
    def _build_description(product: ProductResponse) -> str:
        """
        Desc ưu tiên: seoDescription → shortDescription → description (cắt câu hoàn chỉnh).
        Không để cắt ngang giữa từ bằng cách truncate đến khoảng trắng gần nhất.
        """
        raw: Optional[str] = (
            product.seoDescription
            or product.shortDescription
            or product.description
        )
        if not raw:
            return f"Mua {product.name} chính hãng tại {_SITE_NAME}. Cam kết chất lượng, hỗ trợ 24/7."

        # Tước bỏ HTML tags nếu có (description có thể chứa HTML)
        import re
        raw = re.sub(r'<[^>]+>', '', raw).strip()

        if len(raw) <= _DESC_MAX:
            return raw

        # Cắt đến khoảng trắng gần nhất trước giới hạn để không bị đứt từ
        truncated: str = raw[:_DESC_TRIM]
        last_space: int = truncated.rfind(' ')
        if last_space > _DESC_TRIM - 20:  # Nếu khoảng trắng gần cuối thì cắt ở đó
            truncated = truncated[:last_space]
        return truncated + "…"

    @staticmethod
    def _build_keywords(product: ProductResponse) -> str:
        """
        Keywords đuôi dài (long-tail) theo chuẩn 2026 Vietnam E-commerce SEO.
        Ưu tiên admin nhập; fallback tự sinh từ tên + category + brand.
        """
        if product.seoKeywords:
            return product.seoKeywords

        name: str = product.name
        cat: str = product.category or ""
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
        Thêm brand, seller và priceValidUntil cho Rich Results.
        """
        effective_price: float = (
            product.discountPrice if product.discountPrice else product.price
        )

        schema: dict = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product.name,
            "description": desc,
            "image": product.images if product.images else [],
            "sku": product.sku or product.id,
            "brand": {
                "@type": "Brand",
                "name": _BRAND_NAME,
            },
            "offers": {
                "@type": "Offer",
                "url": canonical_url,
                "priceCurrency": "VND",
                "price": effective_price,
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

            if review_nodes and count > 0:
                schema["review"] = review_nodes
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
    def generate_seo_meta(product: ProductResponse) -> SeoMetaSchema:
        """
        Entry point: Tạo đầy đủ SEO metadata + JSON-LD cho một sản phẩm.
        Output là SeoMetaSchema (strict-typed), không trả về bất kỳ 'Any'.
        """
        canonical_url: str = f"https://{_BASE_DOMAIN}/{product.slug}"

        title: str = SeoService._build_title(product)
        desc: str = SeoService._build_description(product)
        keywords: str = SeoService._build_keywords(product)
        json_ld: str = SeoService._build_json_ld(product, canonical_url, desc)

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
        )
