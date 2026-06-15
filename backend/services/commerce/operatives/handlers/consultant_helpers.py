from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.services.commerce.operatives.handlers.base import SupportContext

logger = logging.getLogger("arq.worker")

def _wrap_prefix(text: str) -> str:
    if not text.startswith("[z2]"):
        return f"[z2] {text}"
    return text

def _generate_fast_db_consultation(ctx: SupportContext) -> Optional[str]:
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

    return _wrap_prefix("\n".join(parts))

def _try_db_product_direct(ctx: SupportContext, msg_norm: str) -> Optional[str]:
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
            fast_reply = _generate_fast_db_consultation(ctx)
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

def _generate_db_fallback(ctx: SupportContext) -> str:
    """Smart DB Fallback: Khi AI lỗi hoặc timeout > 10s, tự động dựng câu trả lời chuyên nghiệp từ DB."""
    # 🚀 Elite V6.2: Order Fallback Guard
    # If in order flow, avoid outputting irrelevant product specs
    if ctx.order_draft and (ctx.order_draft.customer_phone or ctx.order_draft.customer_address or ctx.order_draft.items):
        missing = ctx.order_draft.missing_slots
        if missing:
            missing_str = " và ".join(missing)
            return _wrap_prefix(
                f"Dạ Helen đang xử lý thông tin đơn hàng của mình ạ. ✨ "
                f"Anh/Chị vui lòng cho em xin thêm {missing_str} để em hoàn tất lên bill gửi hàng ngay nhé! 🌸"
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
