from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
    from backend.schemas.support import SupportProductInfo

logger = logging.getLogger("arq.worker")

def _wrap_prefix(text: str) -> str:
    if not text.startswith("[z2]"):
        return f"[z2] {text}"
    return text

async def build_marketing_benefits_block(db: AsyncSession, p_info: SupportProductInfo, dna: Optional[NeuralDNA]) -> str:
    from backend.database.models.promotion import Voucher, ComboDeal
    from backend.database.models.commerce import ProductBase
    from backend.services.commerce.promotion import PromotionService
    from backend.services.commerce.loyalty import LoyaltyService
    from datetime import datetime, timezone
    from sqlalchemy import select, and_, or_
    from sqlalchemy.orm import selectinload

    now = datetime.now(timezone.utc)
    
    combo_desc = "Mua combo nhận thêm quà tặng đặc biệt."
    try:
        prod_stmt = (
            select(ProductBase)
            .options(selectinload(ProductBase.variants))
            .where(ProductBase.id == p_info.id)
        )
        prod_res = await db.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        
        combo_lines = []
        if product and product.variants:
            def get_combo_qty(v) -> int:
                attrs = v.attributes or {}
                return int(attrs.get("combo_qty") or attrs.get("comboQty") or 1)
            
            sorted_vars = sorted(product.variants, key=get_combo_qty)
            has_combos = any(get_combo_qty(v) > 1 for v in sorted_vars)
            
            if has_combos:
                for v in sorted_vars:
                    c_qty = get_combo_qty(v)
                    opt_name = ""
                    tier_idx = v.tier_index
                    if tier_idx and product.tier_variations:
                        names = []
                        for i, idx in enumerate(tier_idx):
                            if i < len(product.tier_variations):
                                opts = product.tier_variations[i].get("options", [])
                                if isinstance(opts, list) and idx < len(opts):
                                    names.append(str(opts[idx]))
                        opt_name = " - ".join(names)
                    else:
                        opt_name = v.sku or f"Gói {c_qty} sp"
                        
                    if opt_name.startswith("Hộp 1 Tuýp") or opt_name.startswith("Combo"):
                        pass
                    else:
                        opt_name = f"Hộp {c_qty} sp" if c_qty == 1 else f"Combo {c_qty} sp"
                    
                    v_price = (v.discount_price or v.price) * c_qty
                    gifts = v.attributes.get("gifts") if v.attributes else None
                    gift_desc = ""
                    if gifts:
                        gift_items = [f"{g.get('qty', g.get('quantity', 1))}x {g.get('name')}" for g in gifts]
                        gift_desc = f" (Tặng {', '.join(gift_items)})"
                    combo_lines.append(f"• **{opt_name}**: {int(v_price):,}đ{gift_desc}".replace(",", "."))
                    
        if combo_lines:
            combo_desc = "\n   " + "\n   ".join(combo_lines)
        else:
            c_stmt = select(ComboDeal).where(
                and_(
                    ComboDeal.deleted_at.is_(None),
                    ComboDeal.is_active == True,
                    or_(ComboDeal.start_date.is_(None), ComboDeal.start_date <= now),
                    or_(ComboDeal.end_date.is_(None), ComboDeal.end_date >= now),
                )
            )
            c_rows = (await db.execute(c_stmt)).scalars().all()
            for c in c_rows:
                cond = c.condition_payload or {}
                p_ids = cond.get("product_ids", [])
                p_ids_str = [str(pid) for pid in p_ids]
                if not p_ids_str or str(p_info.id) in p_ids_str:
                    rwd = c.reward_payload or {}
                    buy_qty = cond.get("buy_qty", 2)
                    get_qty = rwd.get("get_qty", 1)
                    combo_desc = f"Mua {buy_qty} tặng {get_qty} (Ưu đãi {c.name})"
                    break
    except Exception as e:
        logger.warning(f"[MarketingBlock] Combo query failed: {e}")

    voucher_desc = "Không có voucher khả dụng cho sản phẩm này."
    try:
        v_stmt = select(Voucher).where(
            and_(
                Voucher.deleted_at.is_(None),
                Voucher.is_active == True,
                or_(Voucher.is_viral == False, Voucher.is_viral.is_(None)),
                or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
            )
        ).order_by(Voucher.priority.desc())
        v_rows = (await db.execute(v_stmt)).scalars().all()
        
        discount_vouchers = []
        shipping_vouchers = []
        subtotal = float(p_info.price or 0.0)
        
        for v in v_rows:
            if subtotal < (v.min_spend or 0):
                continue
            if v.type == "SHIPPING":
                shipping_vouchers.append(v)
            else:
                discount_vouchers.append(v)
                
        best_disc_v = None
        max_disc_sav = 0.0
        for v in discount_vouchers:
            sav = PromotionService.calculate_voucher_discount(subtotal, v)
            if sav > max_disc_sav:
                max_disc_sav, best_disc_v = sav, v
                
        best_ship_v = None
        max_ship_sav = 0.0
        for v in shipping_vouchers:
            sav = PromotionService.calculate_voucher_discount(subtotal, v)
            if sav > max_ship_sav:
                max_ship_sav, best_ship_v = sav, v
                
        voucher_parts = []
        if best_disc_v:
            cond_str = f" cho đơn hàng từ {int(best_disc_v.min_spend):,}đ".replace(",", ".") if best_disc_v.min_spend else ""
            voucher_parts.append(f"• **Giảm giá**: Nhập mã **`{best_disc_v.id}`** giảm ngay {int(max_disc_sav):,}đ trực tiếp cho sản phẩm này{cond_str}".replace(",", "."))
        if best_ship_v:
            voucher_parts.append(f"• **Vận chuyển**: Nhập mã **`{best_ship_v.id}`** giảm đến {int(max_ship_sav):,}đ phí vận chuyển".replace(",", "."))
            
        if voucher_parts:
            voucher_desc = "\n   " + "\n   ".join(voucher_parts)
    except Exception as e:
        logger.warning(f"[MarketingBlock] Voucher query failed: {e}")

    try:
        from backend.constants.commerce import LoyaltyConfig
        earned_points = int(p_info.price // LoyaltyConfig.EARNING_RATE_VND)
        earned_vnd = earned_points * LoyaltyConfig.POINT_VALUE
        point_val_desc = f"Tích lũy **{earned_points} điểm** (~{earned_vnd:,}đ)".replace(",", ".")
        if dna and dna.available_points > 0:
            points_desc = f"{point_val_desc}. Bạn hiện có **{dna.available_points} điểm** (~{dna.available_points * LoyaltyConfig.POINT_VALUE:,}đ) để dùng ngay!".replace(",", ".")
        else:
            points_desc = f"{point_val_desc} cho đơn sau. Chia sẻ link nhận thêm voucher 20k!"
    except Exception as e:
        logger.warning(f"[MarketingBlock] Loyalty points logic failed: {e}")
        points_desc = "Tích lũy điểm thưởng hấp dẫn cho đơn hàng sau."

    checkin_desc = "Mỗi ngày điểm danh nhận ngay **1 điểm** (10.000đ) miễn phí!"
    try:
        checkin_cfg = await LoyaltyService._get_checkin_config(db)
        cycle_days = checkin_cfg.get("cycle_days", 7)
        rewards = checkin_cfg.get("rewards", [1, 1, 1, 1, 1, 1, 2])
        day1_val = rewards[0] if len(rewards) > 0 else 1
        day7_val = rewards[-1] if len(rewards) > 0 else 2
        checkin_desc = f"Mỗi ngày điểm danh nhận ngay **{day1_val} điểm** ({day1_val * 10}k), ngày thứ {cycle_days} nhận **{day7_val} điểm** ({day7_val * 10}k) miễn phí!"
    except Exception as e:
        logger.warning(f"[MarketingBlock] Check-in config fetch failed: {e}")

    marketing_block = (
        f"🎁 **Ưu đãi độc quyền đang áp dụng:**\n"
        f"1. **Combo Tiết kiệm**: {combo_desc}\n"
        f"2. **Voucher áp dụng**: {voucher_desc}\n"
        f"3. **Tích điểm Osmo**: {points_desc}\n"
        f"4. **Điểm danh nhận quà**: {checkin_desc}"
    )
    return marketing_block

async def _generate_fast_db_consultation(ctx: SupportContext) -> Optional[str]:
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

    # 2. Tạo bộ marketing benefits
    marketing_block = await build_marketing_benefits_block(ctx.db, ctx.p_info, ctx.dna)

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
        marketing_block,
        ""
    ])

    if price_display:
        parts.append(f"💰 **Giá ưu đãi độc quyền**: {price_display}")
        
    parts.extend([
        "",
        "💬 Để không bỏ lỡ chương trình ưu đãi đặc biệt hôm nay, **Anh/Chị nhắn ngay Số Điện Thoại + Địa Chỉ** để Helen hỗ trợ lên đơn và gửi quà tặng độc quyền giao tận nơi nhé! 🌸"
    ])

    return _wrap_prefix("\n".join(parts))

async def _try_db_product_direct(ctx: SupportContext, msg_norm: str) -> Optional[str]:
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
            fast_reply = await _generate_fast_db_consultation(ctx)
            if fast_reply:
                return fast_reply
        return None

    p_name = ctx.p_info.name
    price_display = ctx.p_info.price_display
    product_ctx = ctx.product_ctx

    # Build marketing block
    marketing_block = await build_marketing_benefits_block(ctx.db, ctx.p_info, ctx.dna)

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
                f"{marketing_block}\n\n"
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
                f"{marketing_block}\n\n"
                f"Sản phẩm 100% chính hãng, nhập khẩu nguyên đai nguyên kiện, đầy đủ hồ sơ pháp lý chuẩn Bộ Y Tế Việt Nam ạ. "
                f"Anh/Chị yên tâm đặt hàng nhé! 🌸"
            )
    return None

def _generate_db_fallback(ctx: SupportContext) -> str:
    """Smart DB Fallback: Khi AI lỗi hoặc timeout > 10s, tự động dựng câu trả lời chuyên nghiệp từ DB."""
    # 🚀 Elite V6.2: Order Fallback Guard
    # If in order flow, avoid outputting irrelevant product specs
    import re
    msg_clean = ctx.request.message.lower().strip()
    is_checkout_msg = any(kw in msg_clean for kw in ["tính tiền", "tinh tien", "thanh toán", "thanh toan", "mua", "đặt", "lấy", "ship", "giao", "chốt", "lên đơn", "order", "checkout"])
    
    from backend.schemas.support import SupportIntent
    is_order_intent = False
    if hasattr(ctx, "intent") and ctx.intent:
        is_order_intent = ctx.intent in (SupportIntent.PURCHASE, SupportIntent.ORDER_STATUS)
    
    is_order_flow = (
        (ctx.order_draft and (ctx.order_draft.customer_phone or ctx.order_draft.customer_address or ctx.order_draft.items))
        or bool(ctx.request.cart_items)
        or is_checkout_msg
        or is_order_intent
    )

    if is_order_flow:
        if ctx.order_draft:
            missing = ctx.order_draft.missing_slots
        else:
            missing = []
            if not re.search(r"0\d{8,10}", msg_clean):
                missing.append("Số điện thoại")
            if "/" not in msg_clean and not any(kw in msg_clean for kw in ["đường", "phố", "phường", "quận", "huyện", "xã", "tỉnh", "tp", "hcm", "hn"]):
                missing.append("Địa chỉ cụ thể")

        if missing:
            missing_str = " và ".join(missing)
            return _wrap_prefix(
                f"Dạ Helen đang kết nối lại với hệ thống tạo đơn. ✨ "
                f"Anh/Chị vui lòng cho em xin thêm {missing_str} để em hỗ trợ lên bill và giao hàng tận nơi cho mình ngay nhé! 🌸"
            )
        else:
            return _wrap_prefix(
                "Dạ Helen đang kết nối lại với hệ thống tạo đơn. Đơn hàng của mình đang được xử lý, "
                "chuyên viên bên em sẽ gọi điện xác nhận cho mình ngay lập tức ạ! Anh/Chị yên tâm nhé! 🌸"
            )

    if not ctx.product_ctx or not ctx.p_info:
        # Fallback cho các câu hỏi chính sách/tuyển dụng/CTV hoặc không có ngữ cảnh sản phẩm
        return (
            "Dạ hiện tại hệ thống tư vấn thông tin chi tiết chính sách/tuyển dụng của Osmo đang bận xử lý dữ liệu. "
            "Để không làm mất thời gian của Anh/Chị, mình vui lòng liên hệ Hotline/Zalo OA của Osmo hoặc để lại số điện thoại "
            "kèm yêu cầu tại đây nhé. Chuyên viên của bên em sẽ chủ động liên hệ lại hỗ trợ mình ngay lập tức ạ! 🌸"
        )
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
    return _wrap_prefix("\n".join(parts))
