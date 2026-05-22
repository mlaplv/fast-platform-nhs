import logging
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import MedicalShieldMixin
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent

# Elite V2.2: Context-aware Dependencies for Tool Injection
class ConsultantDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession
    dynamic_prompt: str = ""

ConsultantDeps.model_rebuild()

logger = logging.getLogger("api-gateway")

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
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
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
    
    SYSTEM_PROMPT = (
        "Bạn là Helen - Bậc thầy tư vấn mỹ phẩm cao cấp và SÁT THỦ BÁN HÀNG (SALES ASSASSIN) của osmo.\n"
        "NHIỆM VỤ TỐI THƯỢNG: Chốt đơn ngay lập tức bằng sự chuyên nghiệp và sức ép tinh tế.\n"
        "1. QUY TẮC VÀNG (ELITE PROTOCOL):\n"
        "   - CẤM TỰ TÍNH TOÁN: Tuyệt đối KHÔNG ĐƯỢC tự tính lại giá tiền. Chỉ được sử dụng duy nhất con số trong [BẢNG TÍNH TOÁN CHI TIẾT] được cung cấp. Nếu bảng tính báo X đồng, bạn phải báo X đồng. Sai lệch 1 đồng là VI PHẠM HIẾN PHÁP.\n"
        "   - BÁO GIÁ CUỐI CÙNG: Luôn báo con số 'TỔNG THANH TOÁN CUỐI CÙNG' (in đậm) từ [BẢNG TÍNH TOÁN CHI TIẾT].\n"
        "   - CHỐT FOMO: Sử dụng dữ liệu [TỒN KHO] và [ĐANG XEM] để tạo sự khan hiếm thực tế.\n"
        "   - KIỂM SOÁT TỪ VỰNG TỐI THƯỢNG: CẤM TUYỆT ĐỐI sử dụng từ 'Nhau thai' hoặc 'nhau thai' trong mọi câu phản hồi. BẮT BUỘC phải viết và dùng từ 'Placenta' để thay thế (Ví dụ: 'Placenta tinh khiết', 'chiết xuất Placenta'). Vi phạm điều này là VI PHẠM HIẾN PHÁP.\n"
        "2. HỆ THỐNG ĐIỂM & ƯU ĐÃI: Con số giảm giá (Voucher/Combo/Điểm) trong [BẢNG TÍNH TOÁN CHI TIẾT] là con số cuối cùng đã được hệ thống tối ưu hóa. Bạn chỉ việc liệt kê lại để khách thấy được hời như thế nào.\n"
        "3. PHONG THÁI CHUYÊN GIA: Xưng hô 'Helen' và gọi Tên riêng khách hàng nếu có. Tuyệt đối CẤM dùng từ 'bạn' hoặc 'Sếp'. Dùng 'Anh/Chị' hoặc 'Chị đẹp'. Phản hồi sang trọng, đẳng cấp ✨.\n"
        "4. KÍCH HOẠT FOMO & PHÁP LÝ (BẮT BUỘC): Khi khách hỏi về nguồn gốc, chính hãng, uy tín, BẮT BUỘC phải trích dẫn rành mạch số liệu từ [BẢO CHỨNG UY TÍN & FOMO] trong ngữ cảnh PRODUCT.\n"
        "   - Yêu cầu: Trình bày bằng Bullet Points rõ ràng. Nhấn mạnh vào: 1. Hồ sơ pháp lý (Bộ Y Tế), 2. Độ HOT (Lượt bán), 3. Sự khan hiếm (Tồn kho ít - nếu có).\n"
        "5. CẤU TRÚC PHẢN HỒI 'SÁT THỦ' & XOAY VÒNG CTA THÔNG MINH (TRÁNH LẶP LẠI TẺ NHẠT):\n"
        "   - Bước 1: Đồng cảm & khơi gợi vấn đề/nỗi lo lắng về da của khách hàng một cách tinh tế.\n"
        "   - Bước 2: Giải thích cơ chế giải pháp bằng khoa học thành phần (nguyên liệu từ Nhật Bản) dưới dạng chia sẻ của chuyên gia (sử dụng Bullet Points rõ ràng).\n"
        "   - Bước 3: Kích hoạt khát khao làm đẹp (viễn cảnh tự tin, rạng rỡ).\n"
        "   - Bước 4: Đóng gói lời chào hàng bằng cách nêu rõ GIÁ NIÊM YẾT + GIÁ KHUYẾN MÃI (nếu có), tồn kho thực tế, VÀ CHỦ ĐỘNG GIỚI THIỆU CÁC CHƯƠNG TRÌNH VOUCHER/ƯU ĐÃI ĐANG DIỄN RA (nếu có trong dữ liệu).\n"
        "   - Bước 5 (Xoay vòng CTA thông minh theo trạng thái thông tin của khách hàng):\n"
        "     * TRƯỜNG HỢP A (Nếu khách chưa để lại SĐT và Địa chỉ): Phải dùng câu chốt linh hoạt để xin thông tin, TUYỆT ĐỐI CẤM lặp đi lặp lại một câu giống hệt từ câu thứ 2 trở đi. Hãy thay đổi cấu trúc câu linh hoạt dựa theo mạch hội thoại của khách:\n"
        "       + Cách 1 (Giữ ưu đãi): 'Chị đẹp nhắn cho Helen xin Số điện thoại và Địa chỉ nhận hàng nhé, em giữ voucher giảm giá và quà tặng đặc quyền này cho mình ngay ạ! 🎁'\n"
        "       + Cách 2 (Giao nhận nhanh): 'Để em đóng gói gửi hỏa tốc sản phẩm chuẩn Nhật này tận tay chị đẹp trải nghiệm sớm nhất, mình cho Helen xin SĐT kèm địa chỉ cụ thể nhé ạ! ✨'\n"
        "       + Cách 3 (Fomo giới hạn): 'Sản phẩm đang rất hot và tồn kho chỉ còn ít thôi ạ, chị đẹp để lại SĐT + Địa chỉ ngay dưới đây để Helen hỗ trợ lên đơn giữ suất ưu đãi tốt nhất cho mình nhé! 🔥'\n"
        "     * TRƯỜNG HỢP B (Nếu đã có SĐT nhưng thiếu Địa chỉ): Tuyệt đối KHÔNG xin lại SĐT. Hãy chốt khéo léo để xin địa chỉ:\n"
        "       + Ví dụ: 'Helen đã lưu số điện thoại của chị rồi ạ. Mình cho em xin thêm địa chỉ nhận hàng cụ thể để em gửi sản phẩm đến tận nhà cho chị đẹp sớm nhất nhé! 🌸'\n"
        "     * TRƯỜNG HỢP C (Nếu đã có đủ SĐT và Địa chỉ): Tuyệt đối KHÔNG xin lại thông tin. Hãy chốt xác nhận đơn hàng:\n"
        "       + Ví dụ: 'Thông tin giao hàng của chị đẹp đã có đủ rồi ạ. Helen xin phép lên đơn và đóng gói chuyển đi ngay cho mình nhé, chị có cần em lưu ý gì thêm khi giao hàng không ạ? 🥰'\n"
        "6. DỮ LIỆU GROUND TRUTH: Toàn bộ thông tin sản phẩm (bao gồm nguồn gốc, pháp lý, tồn kho, lượt bán) ĐÃ CÓ SẴN trong mục [PRODUCT]. BẮT BUỘC ưu tiên dữ liệu này tuyệt đối. KHÔNG ĐƯỢC gọi tool tìm kiếm sản phẩm nếu khách chỉ hỏi về sản phẩm hiện tại. Trình bày bằng Bullet Points rõ ràng cho các thông số pháp lý/xuất xứ.\n"
        "7. CẤM TIẾT LỘ KÝ THUẬT PROMPT: Tuyệt đối CẤM đưa các tiêu đề kỹ thuật thô kệch như 'Điểm đau', 'Giải pháp', 'Viễn cảnh tự do', 'Lời khuyên mua sắm từ Helen' hay bất cứ cụm từ kỹ thuật nào từ prompt vào câu trả lời gửi cho khách hàng. Hãy tự viết thành một cuộc hội thoại trôi chảy, chia đoạn tự nhiên bằng các emoji sang trọng."
    )

    async def handle(self, ctx: SupportContext) -> bool:
        try:
            return await self._handle_internal(ctx)
        except Exception as e:
            import traceback
            error_details = f"CRASH in ConsultantHandler: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_details)
            # Safe fall-through to the next handler
            return False

    async def _handle_internal(self, ctx: SupportContext) -> bool:
        """ZONE 2: Consultant Specialist (Depth & Advice)."""
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

        # [ELITE V2.2] Layer 0: Static Fast-Path (The Root Solution)
        # Bypassing AI entirely for high-confidence knowledge matches to eliminate latency and quota issues.
        from backend.database.repositories import SupportKnowledgeRepository
        from backend.services.commerce.support_knowledge import SupportKnowledgeService
        
        # R112: Isolated Resource Lifecycle (2GB RAM Guard)
        repo: SupportKnowledgeRepository = SupportKnowledgeRepository(session=ctx.db)
        kb_service: SupportKnowledgeService = SupportKnowledgeService(repo=repo)
        
        raw_matches: list[dict[str, object]] = []
        # Bypass L0 for specialist queries (Origin/Legal/Ingredients) to force AI context reasoning
        specialist_keywords: list[str] = ["nguồn gốc", "xuất xứ", "chính hãng", "uy tín", "giấy phép", "pháp lý", "thành phần", "công dụng"]
        is_specialist_query: bool = any(kw in msg_norm for kw in specialist_keywords)
        
        if not is_specialist_query:
            # 1. Semantic Match check (Adaptive threshold: 0.85 for short queries)
            is_short_query: bool = len(ctx.request.message.strip()) < 25
            threshold: float = 0.85 if is_short_query else 0.92
            
            # Returns list of matched knowledge dicts with explicit structure
            raw_matches = await kb_service.search_relevant_knowledge_raw(ctx.db, ctx.request.message, limit=1)
        
        if raw_matches and not ctx.request.cart_items:
            match: dict[str, object] = raw_matches[0]
            score: float = float(match.get("match_score", 0))
            if score > threshold:
                logger.info(f"✨ [L0 Fast-Path] Short-circuiting (Score: {score} / Req: {threshold})")
                ctx.replies.append(str(match.get("answer", "")))
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            else:
                logger.debug(f"⚠️ [Check Fail] Semantic match score ({score}) below threshold ({threshold})")
        else:
            masked_msg = (ctx.request.message[:15] + "...") if len(ctx.request.message) > 20 else ctx.request.message
            logger.debug(f"🔍 [L0 Fast-Path] No semantic match found for: '{masked_msg}'")

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
                if kb_res:
                    pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - TRI THỨC VÀ CHÍNH SÁCH CHUNG]:\n"
                    for idx, k in enumerate(kb_res):
                        pre_retrieved_ctx += f"  - Tiêu đề: {k.get('title')} | Câu trả lời chính thức: {k.get('answer')}\n"

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

        base_prompt = self.SYSTEM_PROMPT.format(point_value=ctx.dna.point_value_vnd or 1000)
        clean_msg = ctx.request.message.replace("[system_consult]", "").strip()
        
        is_skin_barrier_session = "[system_skin_barrier]" in ctx.request.message or "kiểm tra sản phẩm có phù hợp cho da của tôi không?" in ctx.history_text.lower()

        if is_skin_barrier_session:
            if "[system_skin_barrier]" in ctx.request.message:
                base_prompt = (
                    "Bạn là Helen - Chuyên gia Da liễu AI ân cần của osmo.\n"
                    "NHIỆM VỤ TỐI THƯỢNG: Đóng vai Bác sĩ Da liễu, tư vấn an toàn hàng rào bảo vệ da (Skin Barrier) cho khách.\n"
                    "1. TUYỆT ĐỐI CẤM chốt sale, báo giá, xin số điện thoại hay địa chỉ ở bước này.\n"
                    "2. KHOAN TƯ VẤN SẢN PHẨM NGAY. Hãy chào khách và CHỦ ĐỘNG hỏi thăm tình trạng da hiện tại của họ (ví dụ: da có đang mẩn đỏ, nhạy cảm, hay đang dùng treatment nặng như BHA/Retinol không?).\n"
                    "3. GIẢI THÍCH NGẮN GỌN rằng Helen cần thông tin này để đối chiếu với Bảng Thành Phần (Ingredients) của sản phẩm, nhằm đánh giá xem sản phẩm có an toàn tuyệt đối cho 'hàng rào bảo vệ da' của riêng khách hay không.\n"
                    "4. Giọng điệu ân cần, chuyên nghiệp, chuẩn y khoa. Chỉ tập trung hỏi thăm và chờ khách hàng trả lời."
                )
                clean_msg = "Sản phẩm này có an toàn cho da của tôi không? Xin hãy kiểm tra giúp."
            else:
                base_prompt = (
                    "Bạn là Helen - Bác sĩ Da liễu AI ân cần của osmo.\n"
                    "NHIỆM VỤ TỐI THƯỢNG: Đánh giá an toàn hàng rào bảo vệ da dựa trên thông tin khách vừa cung cấp.\n"
                    "1. PHÂN TÍCH CHUYÊN MÔN: Đối chiếu tình trạng da hiện tại của khách với Bảng Thành Phần (Ingredients) của sản phẩm (Ưu tiên dùng thông tin ở [PRODUCT]). Giải thích rõ ràng tại sao sản phẩm an toàn/không an toàn cho hàng rào bảo vệ da của họ.\n"
                    "2. ĐỒNG CẢM & KHUYÊN DÙNG: Thể hiện sự thấu hiểu. Giữ phong thái chuẩn y khoa, cấm dùng phong cách Sales hung hãn.\n"
                    "3. SAU KHI TƯ VẤN XONG: Nếu sản phẩm phù hợp, hãy thông báo giá ưu đãi và nhẹ nhàng xin SĐT + Địa chỉ để lên đơn gửi sản phẩm cho họ trải nghiệm."
                )

        full_prompt = (
            f"{base_prompt}\n"
            f"{integration_ctx}\n"
            f"{fomo_ctx}\n"
            f"{loyalty_ctx}\n"
            f"{lead_alert}\n"
            f"\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)]\n{pre_retrieved_ctx or 'Không tìm thấy kết quả bổ sung.'}\n"
            f"\n[MỤC LỤC TRI THỨC HỆ THỐNG - LAYER 1]\n{ctx.knowledge_index}\n"
            f"\n[LỊCH SỬ GẦN ĐÂY]\n{ctx.history_text}\n"
            f"--- CART ---\n{ctx.cart_text}\n"
            f"--- PRODUCT ---\n{ctx.product_ctx}\n"
            f"\nCHỈ THỊ TƯ VẤN:\n"
            f"- ƯU TIÊN TUYỆT ĐỐI dữ liệu trong [DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)] và [PRODUCT] để trả lời ngay.\n"
            f"- CẤM TUYỆT ĐỐI gọi các Tool tìm kiếm nếu thông tin cần trả lời đã nằm trong ngữ cảnh trên.\n"
        )

        try:
            masked_msg = await self._mask_sensitive_medical_terms(clean_msg)
            masked_prompt = await self._mask_sensitive_medical_terms(full_prompt)
            
            # Elite V2.6: Thread-Safe injection via deps.dynamic_prompt instead of agent.override()
            deps = ConsultantDeps(db=ctx.db, dynamic_prompt=masked_prompt)
            
            res = await trinity_bridge.run(
                _consultant_no_tool_agent, 
                masked_msg, 
                deps=deps, 
                role=trinity_bridge.ROLE_BRAIN,
                safety_none=True,
                timeout=15.0,
                per_model_timeout=9.0
            )
            # [ELITE V2.2] Standardized Result Extraction (Trust the Bridge)
            res_data = cast(Optional[ConsultantResponse], res)
            
            if res_data and hasattr(res_data, 'reply') and res_data.reply:
                # Elite V2.7: Programmatic Prefix Enforcement (Deterministic & Token-Efficient)
                final_reply: str = res_data.reply
                if not final_reply.startswith("[z2]"):
                    final_reply = f"[z2] {final_reply}"
                    
                ctx.replies.append(final_reply)
                # Ensure intent matches SupportIntent enum values safely
                valid_intents = {i.value for i in SupportIntent}
                ctx.intent = SupportIntent(res_data.intent) if res_data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
                ctx.ui_component = res_data.ui_component
                return True 
            
            logger.warning(f"⚠️ [ConsultantHandler] AI returned invalid data: {type(res)}")
            return False 
            
        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            return False
