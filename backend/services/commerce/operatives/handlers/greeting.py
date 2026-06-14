import os
import logging
import unicodedata
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext

logger = logging.getLogger("api-gateway")

class GreetingHandler(BaseHandler):
    """
    ZONE 1: Persona Greeting Specialist (osmo Elite V2.6).
    Priority: Build rapport, set Vibe, and plant a sales hook.
    """

    async def _build_promo_hook(self, ctx: SupportContext) -> str:
        """Query DB for active promotions to build a real-time sales hook."""
        try:
            from backend.database.models.promotion import Voucher, ComboDeal
            from backend.database import current_tenant_id
            tid = current_tenant_id.get() or "default"
            now = datetime.now(timezone.utc)

            # Query active combos
            combo_stmt = select(ComboDeal.name, ComboDeal.type, ComboDeal.condition_payload, ComboDeal.reward_payload).where(
                and_(
                    ComboDeal.deleted_at.is_(None), ComboDeal.is_active == True, ComboDeal.tenant_id == tid,
                    or_(ComboDeal.start_date.is_(None), ComboDeal.start_date <= now),
                    or_(ComboDeal.end_date.is_(None), ComboDeal.end_date >= now),
                )
            ).limit(2)
            combo_rows = (await ctx.db.execute(combo_stmt)).fetchall()

            # Query best voucher (highest value)
            voucher_stmt = select(Voucher.id, Voucher.title, Voucher.type, Voucher.value, Voucher.max_discount).where(
                and_(
                    Voucher.deleted_at.is_(None), Voucher.is_active == True, Voucher.tenant_id == tid,
                    or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                    or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
                )
            ).order_by(Voucher.priority.desc()).limit(1)
            voucher_row = (await ctx.db.execute(voucher_stmt)).first()

            hooks: list[str] = []
            if combo_rows:
                for c in combo_rows:
                    cond = c.condition_payload or {}
                    rwd = c.reward_payload or {}
                    buy_qty = cond.get("buy_qty", "?")
                    get_qty = rwd.get("get_qty", "?")
                    hooks.append(f"**{c.name}** (Mua {buy_qty} Tặng {get_qty})")
            if voucher_row:
                if voucher_row.type == "PERCENT":
                    val_txt = f"giảm {int(voucher_row.value)}%"
                    if voucher_row.max_discount:
                        val_txt += f" (tối đa {int(voucher_row.max_discount):,}đ)".replace(",", ".")
                elif voucher_row.type == "SHIPPING":
                    val_txt = "miễn phí ship"
                else:
                    val_txt = f"giảm {int(voucher_row.value):,}đ".replace(",", ".")
                v_title = voucher_row.title or f"mã {voucher_row.id}"
                hooks.append(f"**{v_title}** ({val_txt})")

            if hooks:
                return " hoặc ".join(hooks)
            return ""
        except Exception as e:
            logger.warning(f"[GreetingHandler] Promo hook query failed: {e}")
            return ""

    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 1: Smart Greeting with Sales Hook (AI-Zero Quota)."""
        # Elite V2.6: NFKC Normalization for accurate Vietnamese string matching
        raw_msg = ctx.request.message.lower().strip()
        msg = unicodedata.normalize("NFKC", raw_msg)
        # Elite V6.2: Specific Intent Keywords that should NEVER be intercepted by GreetingHandler
        intent_keywords = [
            "ctv", "công tác viên", "tuyển dụng", "đại lý", "affiliate", "chiết khấu",
            "mua", "bán", "đặt", "order", "ship", "giao hàng", "giá", "bao nhiêu",
            "chính sách", "bảo hành", "đổi trả", "hoàn tiền", "hủy", "check", "sản phẩm"
        ]
        has_specific_intent = any(ik in msg for kw in intent_keywords for ik in [kw])

        is_first_msg = not ctx.history_text
        keywords = ["chào", "hi", "hello", "dạ", "alo", "helen", "ơi", "shop ơi", "ad ơi"]
        has_greeting = any(kw in msg for kw in keywords)

        # Elite V6.2: Question Guard - NEVER consume if it looks like a specific query
        q_keywords = ["nào", "gì", "đâu", "sao", "thế nào", "bao nhiêu", "ở đâu", "là gì"]
        is_question = "?" in msg or any(q in msg for q in q_keywords)

        # We only handle if:
        # 1. Message explicitly has greeting keywords (has_greeting is True), OR
        # 2. It is first message, extremely short (< 8 chars), and has no specific intent.
        should_greet = (
            has_greeting or 
            (is_first_msg and len(msg) < 8 and not has_specific_intent)
        )

        if should_greet and len(msg) < 30 and not ctx.request.cart_items and not is_question:
            debug_prefix = "[z1] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""

            # Elite V2.5: Time-aware greetings
            hour = datetime.now().hour
            if 5 <= hour < 11:
                time_greet = "buổi sáng tốt lành"
            elif 11 <= hour < 14:
                time_greet = "buổi trưa vui vẻ"
            elif 14 <= hour < 18:
                time_greet = "buổi chiều thuận lợi"
            else:
                time_greet = "buổi tối ấm áp"

            # Elite V3.0: Identify Name
            c_name = ctx.dna.customer_name or ctx.request.customer_name or "Quý khách"
            if c_name == "Khách ẩn danh": c_name = "Quý khách"
            
            pts_msg = ""
            if ctx.dna.available_points > 0:
                money = "{:,.0f}".format(ctx.dna.available_points * ctx.dna.point_value_vnd).replace(",", ".")
                pts_msg = f" Hiện mình đang có **{ctx.dna.available_points} điểm** tích lũy đặc quyền (~{money}đ) đó ạ. "

            if ctx.dna.segment == "VIP":
                prefix = f"{debug_prefix}Dạ Helen thân chào {c_name} - khách quý của osmo! 🌟 Chúc mình một {time_greet} ạ. Thật tuyệt vời khi được gặp lại mình!{pts_msg}"
            elif ctx.dna.segment == "REGULAR":
                prefix = f"{debug_prefix}Dạ Helen chào {c_name}, em rất vui được gặp lại mình trong {time_greet} hôm nay!{pts_msg}"
            else:
                prefix = f"{debug_prefix}Dạ Helen chào {c_name}! Chúc mình một {time_greet} nhé. 🌸 "

            # P0-2 Fix: Query real-time promotions from DB instead of hardcoding
            promo_hook = await self._build_promo_hook(ctx)

            # Elite V5.9: Context-aware Sales Assassin Hook
            if ctx.p_info:
                # Đang ở trang sản phẩm cụ thể - Chốt FOMO & Ưu đãi
                price_tag = f" (**{ctx.p_info.price_display}**)" if ctx.p_info.price_display else ""
                prefix += f"Em thấy mình đang quan tâm đến siêu phẩm **{ctx.p_info.name}**{price_tag} - đây hiện đang là dòng 'best-seller' thăng hạng nhan sắc nhà osmo đó ạ! ✨ "
                
                # Dynamic promo hook from DB
                ctx.replies.append(prefix)
                if promo_hook:
                    ctx.replies.append(
                        f"Hiện tại Helen đang có ưu đãi đặc quyền {promo_hook} dành riêng cho mình khi chốt đơn tại đây. 🌸 "
                        "Anh/Chị có muốn Helen kiểm tra mức giá tốt nhất sau khi áp mã cho mình không ạ?"
                    )
                else:
                    ctx.replies.append(
                        "Anh/Chị muốn Helen tư vấn chi tiết về công dụng, thành phần hay lên đơn luôn cho mình nhé! 🌸"
                    )
            else:
                # Ở Homepage / Category / Cart — Smart Hook
                ctx.replies.append(prefix)
                if promo_hook:
                    ctx.replies.append(
                        f"Bên osmo đang có chương trình ưu đãi đặc quyền {promo_hook} dành cho mình đó ạ! ✨ "
                        "Anh/Chị đang quan tâm dòng sản phẩm nào (Trắng da, Trị nám, Chống lão hóa...) để Helen gửi mình mã giảm giá hời nhất nhé! 🌸"
                    )
                else:
                    ctx.replies.append(
                        "Bên osmo có rất nhiều siêu phẩm chăm sóc da cao cấp đó ạ! ✨ "
                        "Anh/Chị đang quan tâm dòng sản phẩm nào để Helen tư vấn chi tiết nhé! 🌸"
                    )

            return True  # TERMINATE: Pure greeting consumed.

        return False  # Fall-through to Consultant/Order for complex queries

