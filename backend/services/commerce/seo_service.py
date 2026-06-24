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
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.product import ProductResponse, SeoMetaSchema
from backend.database.models.seo import SeoNode, SeoEdge
from backend.utils.schema_mutator import mutate_json_ld

logger = logging.getLogger("api-gateway")

# ── Config từ Env để tránh hardcode ────────────────────────────────────────────
_BASE_DOMAIN: str = os.getenv("APP_DOMAIN", "osmo.vn")
_SITE_NAME: str = os.getenv("SEO_SITE_NAME", "osmo.vn")
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
        """Remove HTML tags and clean up whitespace/entities."""
        if not text:
            return ""
        # Remove tags
        text = _RE_HTML.sub('', text)
        # Decode common HTML entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

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
        entities_json: Optional[list[dict]] = None,
        pillar_url: Optional[str] = None,
        cluster_nodes: Optional[list[tuple[str, str]]] = None,
    ) -> str:
        """
        Build Schema.org JSON-LD: Product + Offer + AggregateRating + Review.
        GEO 2026: @id anchoring, priceValidUntil, brand from metadata.
        """
        effective_price: float = (
            product.discountPrice if product.discountPrice else product.price
        )

        # Brand: ưu tiên attributes.brand hoặc attributes["Thương hiệu"] -> metadata.brand -> env fallback
        brand_name: str = _BRAND_NAME
        if product.attributes and isinstance(product.attributes, dict):
            brand_val = product.attributes.get("brand") or product.attributes.get("Thương hiệu")
            if isinstance(brand_val, str) and brand_val.strip():
                brand_name = brand_val.strip()

        if brand_name == _BRAND_NAME and product.metadata:
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
                "priceValidUntil": f"{date.today().year}-12-31",
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
                "shippingDetails": {
                    "@type": "OfferShippingDetails",
                    "shippingRate": {
                        "@type": "MonetaryAmount",
                        "value": "0",
                        "currency": "VND"
                    },
                    "shippingDestination": {
                        "@type": "DefinedRegion",
                        "addressCountry": "VN"
                    }
                },
                "hasMerchantReturnPolicy": {
                    "@type": "MerchantReturnPolicy",
                    "applicableCountry": "VN",
                    "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnPeriod",
                    "merchantReturnDays": "7",
                    "returnMethod": "https://schema.org/ReturnByMail",
                    "returnFees": "https://schema.org/FreeReturn"
                }
            },
        }

        # GEO V4.0: Freshness signal for AI search engines (Gemini AI Overviews)
        updated_at = getattr(product, "updatedAt", None) or getattr(product, "updated_at", None)
        if updated_at:
            if isinstance(updated_at, datetime):
                schema["dateModified"] = updated_at.strftime("%Y-%m-%d")
            elif isinstance(updated_at, str):
                schema["dateModified"] = updated_at[:10]

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

        # SGE Entity Linking: isPartOf parent Pillar URL
        if pillar_url:
            schema["isPartOf"] = {
                "@type": "WebPage",
                "@id": f"{pillar_url}#webpage",
                "url": pillar_url
            }

        # SGE Entity Linking: hasPart Cluster URLs (for Pillar nodes)
        if cluster_nodes:
            schema["hasPart"] = [
                {
                    "@type": "WebPage",
                    "@id": f"{url}#webpage",
                    "url": url,
                    "name": label
                }
                for url, label in cluster_nodes
                if url
            ]

        # SGE Entity Linking: about & mentions (excluding "brand" type entities and matching brand names to prevent duplicate brand errors)
        if entities_json:
            about_entities = [
                {"@type": "Thing", "name": e["name"]}
                for e in entities_json
                if e.get("entity_type", "").lower() == "ingredient"
                and e.get("name")
                and e["name"].strip().lower() != brand_name.strip().lower()
            ]
            if about_entities:
                schema["about"] = about_entities[:2] if len(about_entities) > 1 else about_entities[0]

            mentions_entities = [
                {"@type": "Thing", "name": e["name"]}
                for e in entities_json
                if e.get("entity_type", "").lower() not in ("brand", "ingredient")
                and e.get("name")
                and e["name"].strip().lower() != brand_name.strip().lower()
                and e["name"].strip().lower() != "miccosmo"  # Hardcoded safety fallback for Miccosmo sub-brands
            ]
            if mentions_entities:
                schema["mentions"] = mentions_entities[:5]

        # SGE Shield: Mutate JSON-LD schema (Shuffle keys only to preserve crawler trust, enable_drop=False)
        entropy_cfg = SeoService._get_entropy_config()
        if entropy_cfg.get("enabled", True):
            schema = mutate_json_ld(
                schema,
                seed=product.slug,
                enable_drop=False,
                drop_probability=0.0,
            )

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
            cat_slug: str = getattr(product, "category_slug", None) or getattr(product, "categorySlug", None) or product.slug.split("-")[0]
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": product.category,
                "item": {"@id": f"{_SITE_URL}/{cat_slug}/"},
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
    async def _resolve_settings(db: Optional[AsyncSession] = None) -> None:
        """Resolve site settings from database or Redis cache dynamically (Elite V2.2)."""
        global _SITE_NAME, _SITE_URL, _BRAND_NAME
        site_name = os.getenv("SEO_SITE_NAME") or "osmo.vn"
        base_domain = os.getenv("APP_DOMAIN") or "osmo.vn"
        site_url = f"https://{base_domain}"
        brand_name = os.getenv("SEO_BRAND_NAME") or "osmo"

        # 1. Try Redis cache first
        try:
            from backend.services.xohi_memory import xohi_memory
            cached = await xohi_memory.client.get("system:settings:primary_config")
            if cached:
                cfg = json.loads(cached)
                basic = cfg.get("basic_info", {})
                if basic.get("site_name"):
                    site_name = basic["site_name"]
                if basic.get("domain"):
                    base_domain = basic["domain"]
                    site_url = f"https://{base_domain}"
        except Exception:
            pass

        # 2. Try DB if cache miss or db is passed
        if db and site_name == "osmo.vn":
            try:
                from sqlalchemy import text
                res = await db.execute(text("SELECT value FROM system_settings WHERE key = 'primary_config'"))
                row = res.fetchone()
                if row:
                    cfg = row[0]
                    if isinstance(cfg, str):
                        cfg = json.loads(cfg)
                    basic = cfg.get("basic_info", {})
                    if basic.get("site_name"):
                        site_name = basic["site_name"]
                    if basic.get("domain"):
                        base_domain = basic["domain"]
                        site_url = f"https://{base_domain}"
            except Exception:
                pass

        _SITE_NAME = site_name
        _SITE_URL = site_url
        _BRAND_NAME = brand_name

    @staticmethod
    async def generate_seo_meta(
        product: ProductResponse,
        db: Optional[AsyncSession] = None
    ) -> SeoMetaSchema:
        """
        Entry point: Tạo đầy đủ SEO metadata + JSON-LD cho một sản phẩm.
        Output là SeoMetaSchema (strict-typed), không trả về bất kỳ 'Any'.
        """
        await SeoService._resolve_settings(db)
        canonical_url: str = f"{_SITE_URL}/{product.slug}"

        # Fetch SGE metadata from DB
        intent_type = "unknown"
        entities_json: list[dict] = []
        pillar_url: Optional[str] = None
        cluster_nodes: list[tuple[str, str]] = []

        if db:
            try:
                # Find SEO Node for the product slug
                node_stmt = select(SeoNode).where(
                    SeoNode.node_slug == product.slug,
                    SeoNode.deleted_at.is_(None)
                )
                node = (await db.execute(node_stmt)).scalars().first()
                if node:
                    intent_type = node.intent_type or "unknown"
                    entities_json = node.entities_json or []
                    if not isinstance(entities_json, list):
                        entities_json = []
                    
                    if not entities_json:
                        # Fallback: extract from product metadata
                        metadata_dict = None
                        if hasattr(product, "product_metadata") and product.product_metadata:
                            metadata_dict = product.product_metadata
                        elif hasattr(product, "metadata") and product.metadata:
                            if isinstance(product.metadata, dict):
                                metadata_dict = product.metadata
                            elif hasattr(product.metadata, "model_dump"):
                                metadata_dict = product.metadata.model_dump()
                        
                        if metadata_dict and isinstance(metadata_dict, dict):
                            kg = metadata_dict.get("knowledge_graph")
                            if isinstance(kg, dict) and "entities" in kg:
                                kg_entities = kg["entities"]
                                if isinstance(kg_entities, list):
                                    for e in kg_entities:
                                        if isinstance(e, dict) and "name" in e:
                                            entities_json.append({
                                                "name": e["name"],
                                                "entity_type": e.get("type") or e.get("entity_type") or "unknown"
                                            })
                                    if entities_json:
                                        node.entities_json = entities_json
                                        from sqlalchemy.orm.attributes import flag_modified
                                        flag_modified(node, "entities_json")
                                        try:
                                            await db.commit()
                                        except Exception as commit_err:
                                            logger.warning("[SeoService] Error committing fallback entities_json: %s", commit_err)
                    
                    if node.pillar_url_override:
                        pillar_url = node.pillar_url_override
                    else:
                        # Find parent pillar node url
                        edge_stmt = select(SeoNode.node_url, SeoNode.node_slug, SeoNode.entity_type).join(
                            SeoEdge, SeoEdge.source_node_id == SeoNode.id
                        ).where(
                            SeoEdge.target_node_id == node.id,
                            SeoNode.is_pillar == True,
                            SeoNode.deleted_at.is_(None)
                        )
                        res_parent = (await db.execute(edge_stmt)).first()
                        if res_parent:
                            p_url, p_slug, p_type = res_parent
                            if p_url:
                                pillar_url = p_url
                            else:
                                if p_type == "article":
                                    pillar_url = f"{_SITE_URL}/{p_slug}.html"
                                else:
                                    pillar_url = f"{_SITE_URL}/{p_slug}"

                    # If this node is a pillar, find target cluster nodes
                    if node.is_pillar:
                        cluster_stmt = select(
                            SeoNode.node_url,
                            SeoNode.node_slug,
                            SeoNode.entity_type,
                            SeoNode.node_label
                        ).join(
                            SeoEdge, SeoEdge.target_node_id == SeoNode.id
                        ).where(
                            SeoEdge.source_node_id == node.id,
                            SeoNode.deleted_at.is_(None)
                        )
                        res = (await db.execute(cluster_stmt)).all()
                        for r_url, r_slug, r_type, r_label in res:
                            if r_url:
                                url = r_url
                            else:
                                if r_type == "article":
                                    url = f"{_SITE_URL}/{r_slug}.html"
                                else:
                                    url = f"{_SITE_URL}/{r_slug}"
                            cluster_nodes.append((url, r_label))
            except Exception as e:
                logger.error("[SeoService] Error loading product entity/intent metadata: %s", e)

        # Fallback if entities_json is still empty (either node doesn't exist or node has no entities)
        if not entities_json:
            metadata_dict = None
            if hasattr(product, "product_metadata") and product.product_metadata:
                metadata_dict = product.product_metadata
            elif hasattr(product, "metadata") and product.metadata:
                if isinstance(product.metadata, dict):
                    metadata_dict = product.metadata
                elif hasattr(product.metadata, "model_dump"):
                    metadata_dict = product.metadata.model_dump()
            
            if metadata_dict and isinstance(metadata_dict, dict):
                kg = metadata_dict.get("knowledge_graph")
                if isinstance(kg, dict) and "entities" in kg:
                    kg_entities = kg["entities"]
                    if isinstance(kg_entities, list):
                        for e in kg_entities:
                            if isinstance(e, dict) and "name" in e:
                                entities_json.append({
                                    "name": e["name"],
                                    "entity_type": e.get("type") or e.get("entity_type") or "unknown"
                                })

        # Outbound E-E-A-T Authority Link Injection
        if product.description:
            product.description = SeoService.inject_outbound_authority_links(product.description)

        # ── Live Review Injection: Query system_reviews table (SSOT) ──────────
        # product.metadata.reviews (JSONB static) is NOT synced by ReviewService.
        # We must query the actual SystemReview table for APPROVED reviews.
        if db:
            try:
                from backend.database.models.system import SystemReview
                review_stmt = select(
                    SystemReview.customer_name,
                    SystemReview.customer_location,
                    SystemReview.rating,
                    SystemReview.content,
                ).where(
                    SystemReview.entity_type == "PRODUCT",
                    SystemReview.entity_id == product.id,
                    SystemReview.status == "APPROVED",
                    SystemReview.deleted_at.is_(None),
                ).order_by(SystemReview.created_at.desc()).limit(5)

                review_rows = (await db.execute(review_stmt)).all()
                if review_rows:
                    live_reviews: list[dict] = []
                    for row in review_rows:
                        # Strip HTML tags from review content for clean JSON-LD
                        clean_content = re.sub(r"<[^>]+>", "", row.content or "").strip()
                        live_reviews.append({
                            "name": row.customer_name or "Khách hàng xác thực",
                            "rating": row.rating,
                            "content": clean_content,
                            "location": row.customer_location or "",
                        })
                    # Inject into product.metadata so _build_json_ld reads them
                    if product.metadata:
                        product.metadata.reviews = live_reviews
            except Exception as e:
                logger.warning("[SeoService] Non-blocking: failed to load live reviews for schema: %s", e)

        title: str = SeoService._build_title(product, getattr(product, "seoTitle", None) or getattr(product, "seo_title", None))
        desc: str = SeoService._build_description(product)
        keywords: str = SeoService._build_keywords(product)
        json_ld: str = SeoService._build_json_ld(
            product,
            canonical_url,
            desc,
            entities_json=entities_json,
            pillar_url=pillar_url,
            cluster_nodes=cluster_nodes
        )
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
    async def generate_article_seo_meta(
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
        db: Optional[AsyncSession] = None,
    ) -> "ArticleSeoMeta":
        """GEO 2026: Tạo SEO + SGE Entity-Linked JSON-LD cho trang bài viết."""
        from backend.schemas.article import ArticleSeoMeta
        from sqlalchemy import select
        from backend.database.models.seo import SeoNode, SeoEdge

        await SeoService._resolve_settings(db)
        canonical_url = f"{_SITE_URL}/{slug}.html"
        final_seo_title = seo_title or SeoService._build_title(title)
        
        # Elite V2.2: Prioritize DB-configured seo_description, fallback to excerpt
        desc = seo_description or excerpt or f"Đọc bài viết {title} để biết thêm thông tin chi tiết và hữu ích tại {_SITE_NAME}."
        desc = SeoService._strip_html(desc)
        if len(desc) > _DESC_MAX:
            desc = desc[:_DESC_TRIM] + "…"

        # Fetch SGE metadata from DB
        intent_type = "unknown"
        entities_json: list[dict] = []
        pillar_url: Optional[str] = None

        if db:
            try:
                node_stmt = select(SeoNode).where(
                    SeoNode.node_slug == slug,
                    SeoNode.deleted_at.is_(None)
                )
                node = (await db.execute(node_stmt)).scalars().first()
                if node:
                    intent_type = node.intent_type or "unknown"
                    entities_json = node.entities_json or []
                    
                    if node.pillar_url_override:
                        pillar_url = node.pillar_url_override
                    else:
                        # Find parent pillar node url
                        edge_stmt = select(SeoNode.node_url, SeoNode.node_slug, SeoNode.entity_type).join(
                            SeoEdge, SeoEdge.source_node_id == SeoNode.id
                        ).where(
                            SeoEdge.target_node_id == node.id,
                            SeoNode.is_pillar == True,
                            SeoNode.deleted_at.is_(None)
                        )
                        res_parent = (await db.execute(edge_stmt)).first()
                        if res_parent:
                            p_url, p_slug, p_type = res_parent
                            if p_url:
                                pillar_url = p_url
                            else:
                                if p_type == "article":
                                    pillar_url = f"{_SITE_URL}/{p_slug}.html"
                                else:
                                    pillar_url = f"{_SITE_URL}/{p_slug}"
            except Exception as e:
                logger.error("[SeoService] Error loading entity/intent metadata: %s", e)

        # GEO V4.0: Map intent_type → Schema.org type per Google Article structured data guidelines
        # NewsArticle is reserved for timely news content only
        schema_type = "NewsArticle" if intent_type == "news" else "Article"

        # Build SGE-optimized JSON-LD
        schema: dict = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "@id": f"{canonical_url}#article",
            "headline": title,
            "description": desc,
            "image": [image] if image else [],
            "datePublished": date_published or "2026-01-01",
            "author": {"@type": "Person", "name": author, "url": _SITE_URL},
            "publisher": {"@type": "Organization", "name": _SITE_NAME, "logo": {"@type": "ImageObject", "url": f"{_SITE_URL}/favicon.svg"}},
            "url": canonical_url,
            "inLanguage": "vi",
        }

        # Inject mainEntity if FAQPage and faqs are present
        if schema_type == "FAQPage" and faqs:
            qa_entities: list[dict] = []
            for faq in faqs:
                q = faq.get("question", "")
                a = faq.get("answer", "")
                if q and a:
                    qa_entities.append({
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": a
                        }
                    })
            if qa_entities:
                schema["mainEntity"] = qa_entities

        # SGE Entity Linking: isPartOf parent Pillar URL
        if pillar_url:
            schema["isPartOf"] = {
                "@type": "WebPage",
                "@id": f"{pillar_url}#webpage",
                "url": pillar_url
            }

        # SGE Entity Linking: about & mentions
        if entities_json:
            about_entities = [
                {"@type": "Thing", "name": e["name"]}
                for e in entities_json
                if e.get("entity_type", "").lower() in ("brand", "ingredient") and e.get("name")
            ]
            if about_entities:
                schema["about"] = about_entities[:2] if len(about_entities) > 1 else about_entities[0]

            mentions_entities = [
                {"@type": "Thing", "name": e["name"]}
                for e in entities_json
                if e.get("entity_type", "").lower() not in ("brand", "ingredient") and e.get("name")
            ]
            if mentions_entities:
                schema["mentions"] = mentions_entities[:5]

        # SGE Shield: Mutate JSON-LD schema (Shuffle keys only to preserve crawler trust, enable_drop=False)
        entropy_cfg = SeoService._get_entropy_config()
        if entropy_cfg.get("enabled", True):
            schema = mutate_json_ld(
                schema,
                seed=slug,
                enable_drop=False,
                drop_probability=0.0,
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

        # SGE Shield: Mutate Breadcrumb JSON-LD (Shuffle keys only, enable_drop=False)
        if entropy_cfg.get("enabled", True):
            breadcrumb = mutate_json_ld(breadcrumb, seed=f"{slug}:bc", enable_drop=False, drop_probability=0.0)

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
            "@type": "WebSite",
            "@id": f"{_SITE_URL}#website",
            "url": _SITE_URL,
            "name": name,
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint", "urlTemplate": f"{_SITE_URL}/search?q={{search_term_string}}"},
                "query-input": "required name=search_term_string"
            }
        }

        # Organization (Branding trust for AI Search)
        org_schema = {
            "@type": "Organization",
            "@id": f"{_SITE_URL}#organization",
            "name": name,
            "url": _SITE_URL,
            "logo": f"{_SITE_URL}/favicon.svg",
            "sameAs": [] # Add social links if available
        }

        # GEO V4.0: Gộp WebSite + Organization vào @graph duy nhất
        home_graph: dict = {
            "@context": "https://schema.org",
            "@graph": [website_schema, org_schema]
        }
        return SeoMetaSchema(
            title=final_title,
            description=final_desc,
            keywords=final_keywords,
            canonical_url=canonical_url,
            json_ld_string=json.dumps(home_graph, separators=(",", ":"), ensure_ascii=False),
            breadcrumb_ld_string=""
        )

    @staticmethod
    def inject_outbound_authority_links(html_content: str) -> str:
        """Inject E-E-A-T outbound authority links into HTML content dynamically."""
        if not html_content:
            return html_content

        # Keyword to authority URL mapping
        authority_map = {
            "Tiến sĩ Kenneth K. Hansraj": "https://pubmed.ncbi.nlm.nih.gov/25393825/",
            "Hiệp hội Placenta Nhật Bản": "https://www.jpla.jp/english/",
            "Miccosmo Japan Laboratory": "https://www.miccosmo.co.jp/english/",
            "chiết xuất nhau thai cừu": "https://www.jpla.jp/english/",
            "nhau thai cừu": "https://www.jpla.jp/english/",
            "ceramide tinh khiết": "https://pubmed.ncbi.nlm.nih.gov/31840425/",
            "dầu hạt jojoba": "https://pubmed.ncbi.nlm.nih.gov/24442110/",
            "Harvard Health Publishing": "https://www.health.harvard.edu",
            "Đại học Y Harvard": "https://www.health.harvard.edu",
            "PubMed": "https://pubmed.ncbi.nlm.nih.gov/",
            "ceramide": "https://pubmed.ncbi.nlm.nih.gov/31840425/",
            "collagen": "https://pubmed.ncbi.nlm.nih.gov/30681787/",
        }

        injected_count = 0
        for keyword, url in authority_map.items():
            if injected_count >= 2:
                break
            if keyword in html_content:
                # Split content by existing <a> tags to prevent nested links
                parts = re.split(r'(<a[^>]*>.*?</a>)', html_content, flags=re.IGNORECASE | re.DOTALL)
                changed = False
                for i in range(len(parts)):
                    if i % 2 == 0:  # Text outside <a> tags
                        pattern = re.compile(re.escape(keyword))
                        if pattern.search(parts[i]):
                            parts[i] = pattern.sub(
                                f'<a href="{url}" target="_blank" rel="nofollow noopener noreferrer" class="seo-authority-link">{keyword}</a>',
                                parts[i],
                                count=1
                            )
                            changed = True
                            injected_count += 1
                            break  # Move to next keyword
                if changed:
                    html_content = "".join(parts)

        return html_content
