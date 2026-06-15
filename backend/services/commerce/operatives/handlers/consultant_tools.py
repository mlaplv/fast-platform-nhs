from __future__ import annotations
import logging
from pydantic_ai import RunContext

from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.services.commerce.operatives.handlers.consultant import _consultant_agent, ConsultantDeps

logger = logging.getLogger("arq.worker")

# 🛠️ TOOL LAYER 2: Lấy chi tiết thông tin cửa hàng và sản phẩm chuyên sâu

@_consultant_agent.tool
async def get_shop_profile_tool(ctx_tool: RunContext[ConsultantDeps]) -> str:
    """
    Lấy thông tin chính thức cửa hàng osmo: địa chỉ, hotline, email, giờ làm việc, Zalo, Facebook.
    BẮT BUỘC dùng khi khách hỏi: địa chỉ, liên hệ, hotline, zalo, facebook, giờ hoạt động.
    KHÔNG được đoán. Phải gọi tool này trước khi trả lời.
    """
    import json as _json
    from backend.database.models.system import SystemSetting
    from backend.database import current_tenant_id
    from backend.services.xohi_memory import xohi_memory
    from sqlalchemy import select as _sel

    tid = current_tenant_id.get() or "default"
    raw = await xohi_memory.client.get("system:settings:primary_config")
    
    if raw:
        cfg: dict[str, object] = _json.loads(raw)
    else:
        _row = (await ctx_tool.deps.db.execute(
            _sel(SystemSetting).where(SystemSetting.key == "primary_config")
        )).scalar_one_or_none()
        cfg = dict(_row.value) if _row else {}

    ci: dict[str, object] = cfg.get("contact_info", {})  # type: ignore[assignment]
    bi: dict[str, object] = cfg.get("basic_info", {})    # type: ignore[assignment]
    sm: list[dict[str, object]] = cfg.get("social_media", [])  # type: ignore[assignment]

    zalo = next((str(x.get("url", "")) for x in sm if x.get("platform") == "Zalo"), None)
    fb   = next((str(x.get("url", "")) for x in sm if x.get("platform") == "Facebook"), None)

    site_name = str(bi.get('site_name','osmo'))
    lines: list[str] = [
        f"[THÔNG TIN CỬA HÀNG {site_name.upper()}]",
        f"Địa chỉ: {ci.get('address','Chưa cập nhật')}",
        f"Hotline: {ci.get('hotline','')}",
        f"SĐT: {ci.get('phone','')}",
        f"Email: {ci.get('email','')}",
        f"Giờ làm việc: {ci.get('working_hours','')}",
    ]
    if zalo: lines.append(f"Zalo OA: {zalo}")
    if fb:   lines.append(f"Facebook: {fb}")
    return "\n".join(lines)


@_consultant_agent.tool
async def fetch_product_full_detail(ctx_tool: RunContext[ConsultantDeps], slug: str) -> str:
    """
    Lấy chi tiết đầy đủ 1 sản phẩm: công dụng, thành phần, cách sử dụng, xuất xứ, trọng lượng.
    Nguồn CHÍNH: ProductBase.description (HTML stripped).
    Nguồn PHỤ: product_metadata (ingredients, instructions, origin, weight).
    BẮT BUỘC dùng khi khách hỏi: 'thành phần?', 'cách dùng?', 'công dụng?', 'xuất xứ?'.
    Tham số slug: lấy từ kết quả search_products_tool.
    """
    import re as _re
    from sqlalchemy import select as _sel, and_
    from backend.database.models.commerce import ProductBase
    from backend.database import current_tenant_id

    tid = current_tenant_id.get() or "default"
    stmt = _sel(
        ProductBase.name,
        ProductBase.short_description,
        ProductBase.description,       # Nguồn CHÍNH: HTML rich text admin nhập
        ProductBase.product_metadata,  # Nguồn PHỤ: structured {ingredients, instructions}
        ProductBase.slug,
        ProductBase.price,
        ProductBase.discount_price,
    ).where(and_(
        ProductBase.slug == slug,
        ProductBase.deleted_at.is_(None),
        ProductBase.status == "ACTIVE",
        ProductBase.tenant_id == tid,
    ))
    row = (await ctx_tool.deps.db.execute(stmt)).first()
    if not row:
        return f"[Không tìm thấy sản phẩm '{slug}'. Hãy dùng search_products_tool để tìm đúng slug.]"

    meta: dict[str, object] = row.product_metadata or {}
    price_display = f"{int(row.discount_price or row.price or 0):,}đ".replace(",", ".")

    lines: list[str] = [f"[CHI TIẾT SẢN PHẨM: {row.name} | Giá: {price_display}]"]

    if row.short_description:
        lines.append(f"Tóm tắt: {row.short_description}")

    # Nguồn CHÍNH: strip HTML từ description
    if row.description:
        plain = _re.sub(r"<[^>]+>", " ", str(row.description))
        plain = _re.sub(r"\s+", " ", plain).strip()
        if plain:
            lines.append(f"\nThông tin mô tả đầy đủ:\n{plain[:1500]}")

    # Nguồn PHỤ: structured metadata
    if meta.get("ingredients"):
        lines.append(f"\nThành phần: {meta['ingredients']}")
    if meta.get("instructions"):
        lines.append(f"Cách sử dụng: {meta['instructions']}")
    if meta.get("origin"):
        lines.append(f"Xuất xứ: {meta['origin']}")
    if meta.get("weight"):
        lines.append(f"Trọng lượng/Thể tích: {meta['weight']}")

    return "\n".join(lines)


# 🛠️ TOOL LAYER 3: Tìm kiếm mờ trong Knowledge Base (Semantic Search)
@_consultant_agent.tool
async def search_knowledge_base(ctx_tool: RunContext[ConsultantDeps], query: str) -> str:
    """Tra cứu kho tri thức của osmo khi không thấy ID phù hợp trong Layer 1."""
    repo_tool = SupportKnowledgeRepository(session=ctx_tool.deps.db)
    service_tool = SupportKnowledgeService(repo=repo_tool)
    return await service_tool.search_relevant_knowledge(ctx_tool.deps.db, query)


# 🛠️ TOOL LAYER 4: Tìm kiếm Sản phẩm từ DB
@_consultant_agent.tool
async def search_products_tool(ctx_tool: RunContext[ConsultantDeps], query: str, category: str = "") -> str:
    """
    Tìm kiếm sản phẩm trong cửa hàng osmo theo từ khóa (tên, mô tả, danh mục).
    Dùng khi khách hỏi 'shop có sản phẩm X không?', 'tư vấn sản phẩm cho da Y'.
    Tham số category (tùy chọn): tên danh mục để lọc thêm.
    """
    try:
        from sqlalchemy import select, and_, or_, text
        from backend.database.models.commerce import ProductBase
        from backend.database import current_tenant_id
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
        import asyncio
        
        tid = current_tenant_id.get() or "default"
        encoder = get_shared_encoder()
        rows = []
        db = ctx_tool.deps.db
        
        # 1. Thử Vector Search trước
        if encoder:
            loop = asyncio.get_running_loop()
            vecs = await loop.run_in_executor(None, lambda: list(encoder.embed([query])))
            if vecs:
                vec_str = f"[{','.join(map(str, vecs[0]))}]"
                sql = text("""
                    SELECT p.id, p.name, p.short_description, p.description,
                           p.product_metadata, p.price, p.discount_price, p.stock, p.slug,
                           pe.embedding <=> CAST(:v AS vector) AS dist
                    FROM product_bases p
                    JOIN product_embeddings pe ON p.id = pe.product_base_id
                    WHERE p.deleted_at IS NULL
                      AND p.status = 'ACTIVE'
                      AND p.tenant_id = :tid
                    ORDER BY dist ASC
                    LIMIT 5
                """)
                res = await db.execute(sql, {"v": vec_str, "tid": tid})
                rows = res.fetchall()

        # 2. Fallback Keyword Search nếu vector fail hoặc encoder chưa sẵn sàng
        if not rows:
            kw = f"%{query}%"
            stmt = (
                select(
                    ProductBase.id,
                    ProductBase.name,
                    ProductBase.short_description,
                    ProductBase.description,
                    ProductBase.product_metadata,
                    ProductBase.price,
                    ProductBase.discount_price,
                    ProductBase.stock,
                    ProductBase.slug,
                )
                .where(
                    and_(
                        ProductBase.deleted_at.is_(None),
                        ProductBase.status == "ACTIVE",
                        ProductBase.tenant_id == tid,
                        or_(
                            ProductBase.name.ilike(kw),
                            ProductBase.short_description.ilike(kw),
                            ProductBase.seo_keywords.ilike(kw),
                        )
                    )
                )
                .limit(5)
            )
            rows = (await db.execute(stmt)).fetchall()

        if not rows:
            return f"[Không tìm thấy sản phẩm phù hợp với từ khóa: '{query}']"
            
        lines: list[str] = [f"[KẾT QUẢ SẢN PHẨM - '{query}']"]
        for r in rows:
            price_display = int(r.discount_price or r.price or 0)
            formatted = f"{price_display:,}đ".replace(",", ".")
            stock_txt = f"{r.stock} còn" if r.stock else "Hết hàng"
            lines.append(
                f"- **{r.name}**: {formatted} | Tồn: {stock_txt} | Slug: {r.slug}"
            )
            if r.short_description:
                lines.append(f"  Mô tả: {r.short_description[:120]}")
            meta: dict[str, object] = getattr(r, 'product_metadata', {}) or {}
            if meta.get("ingredients"):
                lines.append(f"  Thành phần: {str(meta['ingredients'])[:100]}...")
            if meta.get("origin"):
                lines.append(f"  Xuất xứ: {meta['origin']}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[ConsultantTool:search_products] Error: {e}")
        return "[Lỗi khi tra cứu sản phẩm, vui lòng thử lại.]"


# 🛠️ TOOL LAYER 5: Lấy Khuyến mãi / Voucher đang active
@_consultant_agent.tool
async def get_active_promotions_tool(ctx_tool: RunContext[ConsultantDeps]) -> str:
    """
    Lấy danh sách tất cả Voucher và Combo Deal đang còn hiệu lực của osmo.
    Dùng khi khách hỏi 'có mã giảm giá không?', 'đang có ưu đãi gì?', 'voucher gì không?'.
    """
    try:
        from sqlalchemy import select, and_, or_
        from backend.database.models.promotion import Voucher, ComboDeal
        from backend.database import current_tenant_id
        from datetime import datetime, timezone
        tid = current_tenant_id.get() or "default"
        now = datetime.now(timezone.utc)

        # --- Vouchers ---
        v_stmt = (
            select(
                Voucher.id,
                Voucher.title,
                Voucher.type,
                Voucher.value,
                Voucher.min_spend,
                Voucher.max_discount,
                Voucher.end_date,
                Voucher.usage_limit,
                Voucher.used_count,
            )
            .where(
                and_(
                    Voucher.deleted_at.is_(None),
                    Voucher.is_active == True,
                    or_(Voucher.is_viral == False, Voucher.is_viral.is_(None)),
                    Voucher.tenant_id == tid,
                    or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                    or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
                )
            )
            .order_by(Voucher.priority.desc())
            .limit(5)
        )
        v_rows = (await ctx_tool.deps.db.execute(v_stmt)).fetchall()

        # --- Combo Deals ---
        c_stmt = (
            select(ComboDeal.name, ComboDeal.type, ComboDeal.condition_payload, ComboDeal.reward_payload)
            .where(
                and_(
                    ComboDeal.deleted_at.is_(None),
                    ComboDeal.is_active == True,
                    ComboDeal.tenant_id == tid,
                    or_(ComboDeal.start_date.is_(None), ComboDeal.start_date <= now),
                    or_(ComboDeal.end_date.is_(None), ComboDeal.end_date >= now),
                )
            )
            .limit(5)
        )
        c_rows = (await ctx_tool.deps.db.execute(c_stmt)).fetchall()

        if not v_rows and not c_rows:
            return "[Hiện tại không có chương trình khuyến mãi nào đang chạy.]"

        lines: list[str] = ["[CHƯƠNG TRÌNH KHUYẾN MÃI ĐANG CHẠY]"]

        if v_rows:
            lines.append("\n📌 Voucher:")
            for v in v_rows:
                remaining = (v.usage_limit - v.used_count) if v.usage_limit else None
                remain_txt = f" | Còn lại: {remaining} lượt" if remaining is not None else ""
                min_txt = f" | Đơn tối thiểu: {int(v.min_spend):,}đ".replace(",", ".") if v.min_spend else ""
                expire_txt = f" | HSD: {v.end_date.strftime('%d/%m/%Y') if v.end_date else 'Không giới hạn'}"
                if v.type == "PERCENT":
                    val_txt = f"Giảm {int(v.value)}%"
                    if v.max_discount:
                        val_txt += f" (tối đa {int(v.max_discount):,}đ)".replace(",", ".")
                elif v.type == "SHIPPING":
                    val_txt = f"Miễn phí ship (giảm tối đa {int(v.value):,}đ)".replace(",", ".")
                else:
                    val_txt = f"Giảm {int(v.value):,}đ".replace(",", ".")
                lines.append(f"  - Mã: **{v.id}** — {v.title or ''} — {val_txt}{min_txt}{remain_txt}{expire_txt}")

        if c_rows:
            lines.append("\n🎁 Combo Deal:")
            for c in c_rows:
                cond = c.condition_payload or {}
                rwd = c.reward_payload or {}
                lines.append(f"  - {c.name}: Mua {cond.get('buy_qty', '?')} Tặng {rwd.get('get_qty', '?')}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[ConsultantTool:get_promotions] Error: {e}")
        return "[Lỗi khi tra cứu khuyến mãi, vui lòng thử lại.]"


# 🛠️ TOOL LAYER 6: Tìm kiếm Bài viết / Chính sách từ DB (News)
@_consultant_agent.tool
async def search_articles_tool(ctx_tool: RunContext[ConsultantDeps], query: str, category: str = "") -> str:
    """
    Tìm kiếm bài viết, tin tức, chính sách của osmo theo từ khóa.
    Dùng khi khách hỏi về chính sách đổi trả, bảo hành, hướng dẫn sử dụng,
    bài viết chia sẻ kiến thức chăm sóc da, hoặc tin tức mới nhất.
    Tham số category (tùy chọn): tên danh mục bài viết để lọc.
    """
    try:
        import re as _re
        from sqlalchemy import select, and_, or_
        from backend.database.models.content import Article
        from backend.database import current_tenant_id
        
        tid = current_tenant_id.get() or "default"
        db = ctx_tool.deps.db
        rows = []

        # 1. Thử Vector Search trước
        try:
            from backend.services.article_vector_service import article_vector_service
            vec_results = await article_vector_service.search_semantic(db, query, limit=3)
            if vec_results:
                rows = vec_results
        except Exception as vec_err:
            logger.warning(f"[ConsultantTool] Article vector search failed: {vec_err}")

        # 2. Fallback Keyword Search nếu vector fail
        if not rows:
            kw = f"%{query}%"
            stmt = (
                select(
                    Article.id,
                    Article.title,
                    Article.excerpt,
                    Article.content,
                    Article.slug,
                    Article.category,
                )
                .where(
                    and_(
                        Article.deleted_at.is_(None),
                        Article.status == "PUBLISHED",
                        Article.tenant_id == tid,
                        or_(
                            Article.title.ilike(kw),
                            Article.excerpt.ilike(kw),
                            Article.seo_keywords.ilike(kw),
                            Article.content.ilike(kw),
                        )
                    )
                )
                .order_by(Article.views.desc())
                .limit(3)
            )
            rows = (await db.execute(stmt)).fetchall()

        if not rows:
            return f"[Không tìm thấy bài viết phù hợp với từ khóa: '{query}']"

        lines: list[str] = [f"[KẾT QUẢ BÀI VIẾT - '{query}']"]
        for r in rows:
            # Safe access for both RowMapping/dict and Row objects
            r_title = r.get("title") if isinstance(r, dict) else getattr(r, "title", "")
            r_category = r.get("category") if isinstance(r, dict) else getattr(r, "category", "")
            r_excerpt = r.get("excerpt") if isinstance(r, dict) else getattr(r, "excerpt", "")
            r_content = r.get("content") if isinstance(r, dict) else getattr(r, "content", "")

            lines.append(f"\n📰 **{r_title}** (Danh mục: {r_category})")
            if r_excerpt:
                lines.append(f"Tóm tắt: {r_excerpt[:200]}")
            elif r_content:
                # Strip HTML tags and take first 500 chars
                plain = _re.sub(r'<[^>]+>', '', str(r_content))[:500]
                lines.append(f"Nội dung: {plain}...")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[ConsultantTool:search_articles] Error: {e}")
        return "[Lỗi khi tra cứu bài viết, vui lòng thử lại.]"
