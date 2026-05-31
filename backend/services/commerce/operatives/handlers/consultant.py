import asyncio
import logging
import traceback
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import MedicalShieldMixin
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent
from backend.services.xohi.prompts import composer
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService

# Elite V2.2: Context-aware Dependencies for Tool Injection
class ConsultantDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession
    dynamic_prompt: str = ""

ConsultantDeps.model_rebuild()

logger = logging.getLogger("arq.worker")

class ConsultantResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str
    intent: str
    ui_component: Optional[str] = None

# Elite V2.2: Module-level Singleton Agents (GC & RAM Optimization)
_consultant_agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
    output_type=ConsultantResponse,
    deps_type=ConsultantDeps
)

_consultant_no_tool_agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
    output_type=ConsultantResponse,
    deps_type=ConsultantDeps
)

@_consultant_agent.system_prompt
def _dynamic_system_prompt(ctx: RunContext[ConsultantDeps]) -> str:
    """Thread-safe dynamic prompt injection via Context deps."""
    return ctx.deps.dynamic_prompt

@_consultant_no_tool_agent.system_prompt
def _dynamic_system_prompt_no_tool(ctx: RunContext[ConsultantDeps]) -> str:
    """Thread-safe dynamic prompt injection for no-tool agent."""
    return ctx.deps.dynamic_prompt

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
            lines.append(f"\n📰 **{r.title}** (Danh mục: {r.category})")
            if r.excerpt:
                lines.append(f"Tóm tắt: {r.excerpt[:200]}")
            elif r.content:
                # Strip HTML tags and take first 500 chars
                plain = _re.sub(r'<[^>]+>', '', str(r.content))[:500]
                lines.append(f"Nội dung: {plain}...")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[ConsultantTool:search_articles] Error: {e}")
        return "[Lỗi khi tra cứu bài viết, vui lòng thử lại.]"

class ConsultantHandler(BaseHandler, MedicalShieldMixin):
    """
    ZONE 2: Pathology and Product Knowledge Specialist.
    Focus: Scientific explanation, trust building, and soft closing.
    """
    
    async def handle(self, ctx: SupportContext) -> bool:
        try:
            return await self._handle_internal(ctx)
        except Exception as e:
            error_details = f"CRASH in ConsultantHandler: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_details)
            # Safe fall-through to the next handler
            return False

    async def _handle_internal(self, ctx: SupportContext) -> bool:
        """ZONE 2: Consultant Specialist (Depth & Advice)."""
        ctx.tool_calls_count += 1
        msg_norm = ctx.request.message.lower().strip()
        
        # 🚀 Elite V2.5: Order Safeguard (Triple-Lock)
        # If the OrderHandler (Priority 2) is active, Consultant must yield when:
        # 1. Message contains a phone number (9+ digits)
        # 2. Message contains address-like patterns (including staff separators : and /)
        # 3. Message contains buying intent keywords.
        has_phone = sum(1 for c in msg_norm if c.isdigit()) >= 9
        has_address_signals = any(kw in msg_norm for kw in ["đường", "phố", "quận", "huyện", "phường", "xã", "tỉnh", "tp", "thành phố", "ngõ", "ngách", "/", ":"])
        buying_intent = any(kw in msg_norm for kw in ["mua", "đặt", "lấy", "ship", "giao", "ok", "chốt", "đơn", "lên đơn", "cho 1 đơn", "cho đơn", "về :"])
        
        if "[system_consult]" in msg_norm or "[system_skin_barrier]" in msg_norm:
            pass
        elif (has_phone or has_address_signals) and buying_intent:
            logger.info(f"🔇 [Consultant Silenced] Yielding to Order Flow: {msg_norm}")
            return False

        # Elite V2.6: Duplicate heuristic (INGREDIENTS/ADDRESS/HOTLINE) removed.
        # L0.5 Sync Heuristic in support_agent.py handles these categories before
        # the pipeline reaches Consultant. No need to duplicate here.

        # --- 🚀 [ELITE V4.2] DATA SYNC GUARD ---
        # If OrderHandler (Priority 2) already filled some lead data, 
        # Consultant MUST use it to avoid asking redundant questions.
        if ctx.lead_data:
            logger.info(f"🛡️ [ConsultantHandler] V4.2 Sync Guard: Found existing lead_data (Phone: {bool(ctx.lead_data.customer_phone)}, Addr: {bool(ctx.lead_data.customer_address)})")
            # If everything is already filled and we are just waiting for chốt đơn,
            # this handler should be very careful or yield back.
            if ctx.lead_data.customer_phone and ctx.lead_data.customer_address and ctx.lead_data.items:
                logger.info("🛡️ [ConsultantHandler] V4.2 Sync Guard: Order complete. Yielding for final chốt đơn.")
                # We return False to let potential Greeting or Order finish, but wait, 
                # OrderHandler already runs before us. If we are here, OrderHandler likely 
                # yielded because it wanted a consultant's touch (Interleaved).

        # ═══════════════════════════════════════════════════════
        # [DB-FIRST LAYER] Kiểm tra dữ liệu sản phẩm trong DB
        # trước khi gọi AI. AI chỉ là DB thứ hai (Elite V6.0)
        # ═══════════════════════════════════════════════════════
        db_direct = self._try_db_product_direct(ctx, msg_norm)
        if db_direct:
            logger.info("✅ [DB-First] Trả kết quả trực tiếp từ DB — AI bypass hoàn toàn")
            ctx.replies.append(db_direct)
            ctx.intent = SupportIntent.PRODUCT_QUERY
            return True

        # [ELITE V6.0] Layer 0: Knowledge Base Fast-Path — Mở rộng cho TẤT CẢ query (không chặn specialist)

        # R112: Isolated Resource Lifecycle (2GB RAM Guard)
        repo: SupportKnowledgeRepository = SupportKnowledgeRepository(session=ctx.db)
        kb_service: SupportKnowledgeService = SupportKnowledgeService(repo=repo)

        is_short_query: bool = len(ctx.request.message.strip()) < 25
        threshold: float = 0.85 if is_short_query else 0.92
        # 1. Search semantically first using pgvector
        raw_matches: list[dict[str, object]] = await kb_service.search_relevant_knowledge_raw(ctx.db, ctx.request.message, limit=1)
        
        # 2. Hybrid Keyword Fallback (ONLY for short queries to prevent false positive keyword mapping on long prompts)
        if not raw_matches or float(raw_matches[0].get("match_score", 0)) <= threshold:
            if is_short_query:
                keyword_matches = await kb_service.search_relevant_knowledge_keyword(ctx.db, ctx.request.message, limit=1)
                # Double lock: only force score if match actually contains a non-empty answer!
                if keyword_matches and str(keyword_matches[0].get("answer", "")).strip():
                    keyword_matches[0]["match_score"] = 1.0
                    raw_matches = keyword_matches

        # 3. Fast-Path decision gate
        if raw_matches and not ctx.request.cart_items:
            match: dict[str, object] = raw_matches[0]
            score: float = float(match.get("match_score", 0))
            ans = str(match.get("answer", "")).strip()
            # Triple lock: score exceeds threshold AND matched answer is valid and non-empty!
            if score > threshold and ans:
                logger.info(f"✨ [L0 KB Fast-Path] Short-circuiting (Score: {score} / Req: {threshold})")
                ctx.replies.append(ans)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            else:
                logger.debug(f"⚠️ [KB Check Fail] score={score} < threshold={threshold} or empty answer")
        else:
            masked_msg = (ctx.request.message[:15] + "...") if len(ctx.request.message) > 20 else ctx.request.message
            logger.debug(f"🔍 [L0 KB] No match for: '{masked_msg}'")

        # RAG Pre-Retrieval: Active RAG Context injection to bypass multiple tool calls
        pre_retrieved_ctx = ""
        try:
            from sqlalchemy import select, and_, or_, text
            from backend.database import current_tenant_id
            from backend.database.models.commerce import ProductBase
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            
            tid = (current_tenant_id.get() or "default")
            msg_clean = ctx.request.message.replace("[system_consult]", "").strip()
            
            if len(msg_clean) > 2:
                # 1. Pre-search products
                p_rows = []
                encoder = get_shared_encoder()
                if encoder:
                    try:
                        vecs = list(encoder.embed([msg_clean]))
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
                                LIMIT 3
                            """)
                            res = await ctx.db.execute(sql, {"v": vec_str, "tid": tid})
                            p_rows = res.fetchall()
                    except Exception as p_err:
                        logger.debug(f"[ConsultantPreRetrieve] Product vector search failed: {p_err}")
                
                if not p_rows:
                    kw = f"%{msg_clean}%"
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
                                )
                            )
                        )
                        .limit(3)
                    )
                    p_rows = (await ctx.db.execute(stmt)).fetchall()

                if p_rows:
                    pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - SẢN PHẨM KHẢ QUAN]:\n"
                    for idx, r in enumerate(p_rows):
                        price_display = int(r.discount_price or r.price or 0)
                        formatted = f"{price_display:,}đ".replace(",", ".")
                        stock_txt = f"{r.stock} còn" if r.stock else "Hết hàng"
                        pre_retrieved_ctx += f"  {idx+1}. {r.name} (Slug: {r.slug}) | Giá: {formatted} | Tồn: {stock_txt}\n"
                        if r.short_description:
                            pre_retrieved_ctx += f"     Mô tả: {r.short_description[:120]}\n"
                        meta = getattr(r, 'product_metadata', {}) or {}
                        if meta.get("ingredients"):
                            pre_retrieved_ctx += f"     Thành phần: {str(meta['ingredients'])[:150]}\n"
                        if meta.get("origin"):
                            pre_retrieved_ctx += f"     Xuất xứ: {meta['origin']}\n"
                
                # 2. Pre-search Knowledge Base / Articles
                kb_res = await kb_service.search_relevant_knowledge_raw(ctx.db, msg_clean, limit=2)
                if not kb_res:
                    kb_res = await kb_service.search_relevant_knowledge_keyword(ctx.db, msg_clean, limit=2)
                if kb_res:
                    pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - TRI THỨC VÀ CHÍNH SÁCH CHUNG]:\n"
                    for idx, k in enumerate(kb_res):
                        pre_retrieved_ctx += f"  - Vấn đề: {k.get('question')} | Hướng giải quyết: {k.get('answer')}\n"

        except Exception as e:
            logger.warning(f"[ConsultantPreRetrieve] Failed pre-retrieval: {e}")

        # Assemble the specialist directive with current context
        lead_alert: str = ""
        if ctx.lead_data:
            if ctx.lead_data.customer_phone and ctx.lead_data.customer_address:
                lead_alert = "\n[SYSTEM ALERT: Khách đã để lại SĐT và Địa chỉ. Hãy xác nhận và chốt đơn ngay!]\n"
            elif ctx.lead_data.customer_phone:
                lead_alert = f"\n[SYSTEM ALERT: Đã có SĐT {ctx.lead_data.customer_phone}, hãy khéo léo xin Địa chỉ để giao hàng.]\n"

        # Integration Alert (Elite V2.2)
        integration_ctx = f"\n[CHẾ ĐỘ TÍCH HỢP]\nZalo OA: {'BẬT' if ctx.zalo_enabled else 'TẮT'}\nMessenger: {'BẬT' if ctx.messenger_enabled else 'TẮT'}\n"
        if not ctx.zalo_enabled:
            integration_ctx += "LƯU Ý: Không gửi link Zalo hoặc nhắc tới Zalo trong hội thoại.\n"
        if not ctx.messenger_enabled:
            integration_ctx += "LƯU Ý: Không nhắc tới Messenger trong hội thoại.\n"

        # Elite V2.6 FOMO Guard: Only inject metrics when real data exists
        fomo_ctx = ""
        if ctx.product_stock and ctx.product_stock > 0:
            fomo_ctx = f"\n[CHỈ SỐ THỰC TẾ]\n[ĐANG XEM]: {ctx.active_visitors} người\n[TỒN KHO]: {ctx.product_stock} sản phẩm\n"

        # Elite V3.0: Loyalty DNA Context
        loyalty_ctx = ""
        if ctx.dna.available_points > 0:
            loyalty_ctx = f"\n[LOYALTY DNA]\nKhách này là {ctx.dna.segment}. Có {ctx.dna.available_points} điểm. (Mức giảm điểm tối đa đã được tính sẵn trong [CART] bên dưới, tuyệt đối không tự tính lại).\n"

        clean_msg = ctx.request.message.replace("[system_consult]", "").strip()
        
        is_skin_barrier_session = "[system_skin_barrier]" in ctx.request.message or "kiểm tra sản phẩm có phù hợp cho da của tôi không?" in ctx.history_text.lower()
        is_system_consult = "[system_consult]" in ctx.request.message

        # Dynamic context dictionary for POS Composer
        composer_context = {
            "point_value": ctx.dna.point_value_vnd or 1000,
            "clean_msg": clean_msg,
            "product_ctx": ctx.product_ctx,
            "history_text": ctx.history_text,
            "cart_text": ctx.cart_text
        }

        if is_skin_barrier_session:
            if "[system_skin_barrier]" in ctx.request.message:
                clean_msg = "Sản phẩm này có an toàn cho da của tôi không? Xin hãy kiểm tra giúp."
                composer_context["clean_msg"] = clean_msg
                base_prompt = composer.compose("helen_consultant_skin_barrier", context=composer_context)
            else:
                base_prompt = composer.compose("helen_consultant_skin_barrier_analysis", context=composer_context)
        elif is_system_consult:
            clean_msg = "Hãy tư vấn chuyên sâu về sản phẩm này giúp tôi."
            composer_context["clean_msg"] = clean_msg
            base_prompt = composer.compose("helen_system_consultation", context=composer_context)
        else:
            base_prompt = composer.compose("helen_consultant_premium", context=composer_context)

        full_prompt = (
            f"{base_prompt}\n"
            f"{integration_ctx}\n"
            f"{fomo_ctx}\n"
            f"{loyalty_ctx}\n"
            f"{lead_alert}\n"
            f"\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)]\n{pre_retrieved_ctx or 'Không tìm thấy kết quả bổ sung.'}\n"
            f"\n[MỤC LỤC TRI THỨC HỆ THỐNG - LAYER 1]\n{ctx.knowledge_index}\n"
            f"\nCHỈ THỊ TƯ VẤN:\n"
            f"- ƯU TIÊN TUYỆT ĐỐI dữ liệu trong [DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)] và [PRODUCT] để trả lời ngay.\n"
            f"- CẤM TUYỆT ĐỐI gọi các Tool tìm kiếm nếu thông tin cần trả lời đã nằm trong ngữ cảnh trên.\n"
        )

        try:
            masked_msg = await self._mask_sensitive_medical_terms(clean_msg)
            masked_prompt = await self._mask_sensitive_medical_terms(full_prompt)

            logger.info(f"🟢 [ConsultantHandler] SYSTEM PROMPT:\n{masked_prompt}")
            logger.info(f"🟢 [ConsultantHandler] USER MESSAGE: {masked_msg}")

            # Elite V6.0: Thread-Safe injection via deps.dynamic_prompt
            deps = ConsultantDeps(db=ctx.db, dynamic_prompt=masked_prompt)

            # ⏱️ Elite V6.0: Cổng bảo vệ 12s - Giảm để kích hoạt Smart DB Fallback sớm hơn khi tải cao
            res = await asyncio.wait_for(
                trinity_bridge.run(
                    _consultant_no_tool_agent,
                    masked_msg,
                    deps=deps,
                    role=trinity_bridge.ROLE_BRAIN,
                    safety_none=True,
                    timeout=12.0,
                    per_model_timeout=5.0
                ),
                timeout=12.0
            )
            # [ELITE V2.2] Standardized Result Extraction (Trust the Bridge)
            res_data = cast(Optional[ConsultantResponse], res)
            
            logger.info(f"🟢 [ConsultantHandler] RAW AI RESPONSE: {res_data}")

            if res_data and hasattr(res_data, 'reply') and res_data.reply:
                # Elite V2.7: Programmatic Prefix Enforcement (Deterministic & Token-Efficient)
                final_reply: str = res_data.reply
                if not final_reply.startswith("[z2]"):
                    final_reply = f"[z2] {final_reply}"
                ctx.replies.append(final_reply)
                valid_intents = {i.value for i in SupportIntent}
                ctx.intent = SupportIntent(res_data.intent) if res_data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
                ctx.ui_component = res_data.ui_component
                return True

            logger.warning(f"⚠️ [ConsultantHandler] AI returned invalid data: {type(res)}")
            # AI returned None/invalid — thử Smart DB Fallback
            db_fallback = self._generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

        except asyncio.TimeoutError:
            logger.warning("⚠️ [ConsultantHandler] AI vượt 10s — Kích hoạt Smart DB Fallback")
            db_fallback = self._generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            db_fallback = self._generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

    def _wrap_prefix(self, text: str) -> str:
        if not text.startswith("[z2]"):
            return f"[z2] {text}"
        return text

    def _generate_fast_db_consultation(self, ctx: SupportContext) -> Optional[str]:
        """Fast-Path DB-First Consultation: Tạo kịch bản bán hàng động siêu tốc (<20ms) cho lượt click đầu tiên."""
        if not ctx.product_ctx or not ctx.p_info:
            return None

        p_name = ctx.p_info.name
        price_display = ctx.p_info.price_display
        product_ctx = ctx.product_ctx

        # 1. Trích xuất thành phần nổi bật (tối đa 4 dòng để ngắn gọn)
        ingredient_lines: list[str] = []
        if "[THÀNH PHẦN NỔI BẬT" in product_ctx:
            lines = product_ctx.split("\n")
            in_section = False
            for line in lines:
                if "[THÀNH PHẦN NỔI BẬT" in line or "[BẢNG THÀNH PHẦN" in line:
                    in_section = True
                elif line.startswith("[") and in_section:
                    break
                elif in_section and line.strip():
                    ingredient_lines.append(line.strip())
        
        ing_text = ""
        if ingredient_lines:
            ing_text = "\n".join(f"🧬 {line}" for line in ingredient_lines[:4])

        # 2. Trích xuất Vouchers đang diễn ra
        voucher_lines: list[str] = []
        for line in ctx.cart_text.split("\n"):
            if line.strip().startswith("- Mã"):
                voucher_lines.append(line.strip().replace("- Mã", "🎟️ Mã"))
        
        promo_text = ""
        if voucher_lines:
            promo_text = "\n" + "\n".join(voucher_lines[:2])

        # 3. Dựng kịch bản Sales Assassin 5 bước siêu súc tích (<250 từ) chuẩn Helen
        parts = [
            f"Dạ Helen chào Anh/Chị! Rất vui được đồng hành cùng Anh/Chị thiết kế liệu trình chăm sóc da hoàn hảo với siêu phẩm **{p_name}** ạ! ✨",
            "",
            f"🌸 **Tại sao {p_name} lại là giải pháp tối ưu cho làn da?**"
        ]
        
        if ing_text:
            parts.append(ing_text)
        else:
            parts.append(f"🧬 Sản phẩm được bào chế với công nghệ hiện đại chuẩn Nhật Bản, cung cấp dưỡng chất thẩm thấu sâu, nuôi dưỡng làn da khỏe mạnh từ gốc tế bào.")

        parts.extend([
            "",
            "✨ **Hiệu quả thực tế:** Sau 14 ngày, làn da sẽ cải thiện rõ rệt, mịn màng, sáng khỏe và củng cố hàng rào bảo vệ da săn chắc hơn.",
            "",
            f"💰 **Ưu đãi độc quyền hôm nay:**"
        ])

        if price_display:
            parts.append(f"• Giá hiện tại: **{price_display}**")
            
        if promo_text:
            parts.append(f"• Quà tặng: Tặng kèm quà độc quyền theo sản phẩm.{promo_text}")
        else:
            parts.append("• Quà tặng: Tặng kèm quà độc quyền theo sản phẩm.")
            
        parts.extend([
            "",
            "💬 Để không bỏ lỡ chương trình ưu đãi đặc biệt hôm nay, **Anh/Chị nhắn ngay Số Điện Thoại + Địa Chỉ** để Helen hỗ trợ lên đơn và gửi quà tặng độc quyền giao tận nơi nhé! 🌸"
        ])

        return self._wrap_prefix("\n".join(parts))

# Duplicate _wrap_prefix removed

    def _try_db_product_direct(self, ctx: SupportContext, msg_norm: str) -> Optional[str]:
        """DB-First Layer: Trả lời trực tiếp từ DB nếu câu hỏi có cấu trúc rõ ràng và DB có đủ dữ liệu."""
        if not ctx.product_ctx or not ctx.p_info:
            return None
        # Câu hỏi hội thoại cá nhân phức tạp → xuống AI
        is_complex_personal = any(kw in msg_norm for kw in [
            "da em", "da mình", "da tôi", "bị mụn", "bị dị ứng",
            "có phù hợp", "có nên dùng", "so sánh", "khác gì", "tốt hơn"
        ])
        if is_complex_personal:
            return None
        # Lượt đầu tiên click "Tư vấn" -> Dùng Fast-Path DB-First Template để phản hồi siêu tốc (<20ms)
        if "[system_consult]" in ctx.request.message:
            if not ctx.history_text.strip():
                fast_reply = self._generate_fast_db_consultation(ctx)
                if fast_reply:
                    return fast_reply
            return None

        p_name = ctx.p_info.name
        price_display = ctx.p_info.price_display
        product_ctx = ctx.product_ctx

        # Trường hợp 1: Hỏi về thành phần / công dụng
        is_ingredient_query = any(kw in msg_norm for kw in [
            "thành phần", "chiết xuất", "nguyên liệu", "công dụng", "tác dụng",
            "chứa chất gì", "chứa gì", "thành phần gì", "có chất gì", "chất gì",
            "dùng để làm gì", "có tác dụng gì", "giúp gì", "trị gì", "chữa gì", "đặc trị"
        ])
        if is_ingredient_query and "[THÀNH PHẦN NỔI BẬT" in product_ctx:
            lines = product_ctx.split("\n")
            ingredient_lines: list[str] = []
            in_section = False
            for line in lines:
                if "[THÀNH PHẦN NỔI BẬT" in line or "[BẢNG THÀNH PHẦN" in line:
                    in_section = True
                elif line.startswith("[") and in_section:
                    break
                elif in_section and line.strip():
                    ingredient_lines.append(line.strip())
            if ingredient_lines:
                ing_text = "\n".join(ingredient_lines)
                price_txt = f"💰 Giá hiện tại: **{price_display}**. " if price_display else ""
                return (
                    f"Dạ đây là thông tin kỹ thuật chính thức từ hãng về **{p_name}** ạ! ✨\n\n"
                    f"🧪 **Thành phần & Công dụng nổi bật:**\n{ing_text}\n\n"
                    f"{price_txt}"
                    f"Anh/Chị muốn Helen tư vấn thêm về cách sử dụng phù hợp với tình trạng da của mình không ạ? 🌸"
                )

        # Trường hợp 2: Hỏi về xuất xứ / chính hãng / pháp lý
        is_origin_query = any(kw in msg_norm for kw in [
            "xuất xứ", "nguồn gốc", "chính hãng", "uy tín", "pháp lý", "chứng nhận", "giấy phép",
            "sản xuất ở đâu", "từ đâu", "nước nào", "của nước nào", "made in"
        ])
        if is_origin_query and "[BẢO CHỨNG UY TÍN" in product_ctx:
            lines = product_ctx.split("\n")
            trust_lines: list[str] = []
            in_section = False
            for line in lines:
                if "[BẢO CHỨNG UY TÍN" in line:
                    in_section = True
                elif line.startswith("[") and in_section:
                    break
                elif in_section and line.strip():
                    trust_lines.append(line.strip())
            if trust_lines:
                trust_text = "\n".join(trust_lines)
                return (
                    f"Dạ để Anh/Chị an tâm tuyệt đối, đây là bảo chứng uy tín chính thức của **{p_name}** ạ! 🛡️\n\n"
                    f"{trust_text}\n\n"
                    f"Sản phẩm 100% chính hãng, nhập khẩu nguyên đai nguyên kiện, đầy đủ hồ sơ pháp lý chuẩn Bộ Y Tế Việt Nam ạ. "
                    f"Anh/Chị yên tâm đặt hàng nhé! 🌸"
                )
        return None

    def _generate_db_fallback(self, ctx: SupportContext) -> str:
        """Smart DB Fallback: Khi AI lỗi hoặc timeout > 10s, tự động dựng câu trả lời chuyên nghiệp từ DB."""
        if not ctx.product_ctx or not ctx.p_info:
            return "Dạ Helen xin lỗi Anh/Chị, hệ thống đang xử lý tải cao. Anh/Chị vui lòng thử lại sau vài giây nhé! 🌸"
        p_name = ctx.p_info.name
        price_display = ctx.p_info.price_display
        lines = ctx.product_ctx.split("\n")
        ingredient_lines: list[str] = []
        trust_lines: list[str] = []
        in_ingredient = False
        in_trust = False
        for line in lines:
            if "[THÀNH PHẦN NỔI BẬT" in line or "[BẢNG THÀNH PHẦN" in line:
                in_ingredient, in_trust = True, False
            elif "[BẢO CHỨNG UY TÍN" in line:
                in_trust, in_ingredient = True, False
            elif line.startswith("[") and (in_ingredient or in_trust):
                in_ingredient, in_trust = False, False
            elif in_ingredient and line.strip():
                ingredient_lines.append(line.strip())
            elif in_trust and line.strip():
                trust_lines.append(line.strip())
        parts: list[str] = [
            f"Dạ Helen đang kết nối lại với hệ thống tư vấn chuyên sâu, để không mất thời gian của Anh/Chị, "
            f"Helen xin gửi ngay thông tin kỹ thuật chính thức của **{p_name}** từ cơ sở dữ liệu hãng ạ! ✨", ""
        ]
        if ingredient_lines:
            parts.append("🧪 **Thành phần & Công dụng nổi bật:**")
            parts.extend(ingredient_lines[:6])
            parts.append("")
        if trust_lines:
            parts.append("🛡️ **Bảo chứng uy tín:**")
            parts.extend(trust_lines[:3])
            parts.append("")
        if price_display:
            parts.append(f"💰 **Giá hiện tại: {price_display}**")
            parts.append("")
        parts.append(
            "Anh/Chị muốn tư vấn thêm hoặc đặt hàng, để lại số điện thoại để chuyên viên liên hệ hỗ trợ chi tiết nhé! 🌸"
        )
        return self._wrap_prefix("\n".join(parts))
