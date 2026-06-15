"""
Context, Pricing & FOMO Helpers — SUPPORT_NAME_CLIENT (Architect's Edition)
========================================================================
Elite V5.5: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations

import logging
import hashlib
import time
import json
import os
import re
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from sqlalchemy import select, and_, desc, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase, ProductVariant, Order, UserLoyalty
from backend.database.models.system import SupportChatHistory, SystemSetting
from backend.database.models.auth import User
from backend.database.models.promotion import Voucher
from backend.schemas.support import SupportRequest, SupportProductInfo, SupportResponse, SupportIntent
from backend.services.commerce.loyalty import LoyaltyService
from backend.services.commerce.operatives.handlers.base import NeuralDNA
from backend.services.xohi_memory import xohi_memory
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
from backend.utils.security import GeminiSecurity

if TYPE_CHECKING:
    from backend.services.commerce.operatives.support_agent import SupportAgentOperative

logger = logging.getLogger("arq.worker")

async def _fetch_chat_context(db: AsyncSession, session_id: str) -> str:
    try:
        stmt = select(
            SupportChatHistory.id,
            SupportChatHistory.role,
            SupportChatHistory.content
        ).where(SupportChatHistory.session_id == session_id).order_by(
            desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)
        ).limit(8)
        result = await db.execute(stmt)
        history_rows = result.all()
        if not history_rows:
            return ""
        h_parts = []
        total_chars = 0
        MAX_TOTAL_CHARS = 8000
        for r in reversed(history_rows):
            h_content = GeminiSecurity.decrypt(r.content or "")
            if h_content == HELEN_FOLLOW_UP_TRIGGER:
                continue
            if len(h_content) > 500:
                h_content = h_content[:500] + "... [TRUNCATED]"
            if r.role == "user":
                from backend.services.commerce.security.input_guard import input_guard
                _safe, _ = input_guard.validate(h_content[:2000])
                if not _safe:
                    logger.warning("[SupportAgent] H-2: Skipping potentially injected history entry, SID: %s", session_id)
                    continue
            if total_chars + len(h_content) > MAX_TOTAL_CHARS:
                break
            h_role = "Khách" if r.role == "user" else "Helen"
            h_parts.append(f"{h_role}: {h_content}")
            total_chars += len(h_content)
        return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n" if h_parts else ""
    except Exception as _e:
        logger.warning("[SupportAgent] _fetch_chat_context failed: %s", _e)
        return ""

async def _fetch_neural_dna(
    db: AsyncSession, session_id: str, lead_phone: Optional[str] = None,
    user_id: Optional[str] = None
) -> NeuralDNA:
    try:
        _sig = hashlib.md5(f"{session_id}:{lead_phone or ''}:{user_id or ''}".encode()).hexdigest()[:12]
        _dna_key = f"support:dna:{_sig}"
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                _cached = await xohi_memory.client.get(_dna_key)
                if _cached:
                    return NeuralDNA.model_validate_json(_cached)
            except Exception as _ce:
                logger.debug("[SupportAgent] DNA cache read failed: %s", _ce)

        mem = await xohi_memory.get_user_context(session_id)
        if mem and "dna" in mem:
            dna_obj = NeuralDNA.model_validate(mem["dna"])
            if not lead_phone and not user_id:
                return dna_obj
        
        final_user_id = user_id
        customer_name = None
        if not final_user_id and lead_phone:
            u_stmt = select(User.id, User.name).where(User.phone == lead_phone).limit(1)
            u_row = (await db.execute(u_stmt)).first()
            if u_row:
                final_user_id = u_row[0]
                customer_name = u_row[1]
        elif final_user_id:
            u_stmt = select(User.name).where(User.id == final_user_id).limit(1)
            customer_name = await db.scalar(u_stmt)

        available_pts = 0
        pt_value = 1000
        if final_user_id:
            if await LoyaltyService.verify_loyalty_integrity(db, final_user_id):
                l_stmt = select(UserLoyalty).where(UserLoyalty.user_id == final_user_id)
                loyalty = (await db.execute(l_stmt)).scalar_one_or_none()
                if loyalty:
                    available_pts = loyalty.available_points
        
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                cached_pt = await xohi_memory.client.get("system:setting:LOYALTY_POINT_VALUE_VND")
                if cached_pt is not None:
                    pt_value = int(cached_pt)
            except Exception:
                pass

        if pt_value == 1000:
            s_stmt = select(SystemSetting).where(SystemSetting.key == "LOYALTY_POINT_VALUE_VND")
            setting = (await db.execute(s_stmt)).scalar_one_or_none()
            if setting and isinstance(setting.value, dict) and "value" in setting.value:
                pt_value = int(setting.value["value"])
                if xohi_memory._use_redis and xohi_memory.client:
                    try:
                        await xohi_memory.client.set("system:setting:LOYALTY_POINT_VALUE_VND", str(pt_value), ex=3600)
                    except Exception:
                        pass

        total_spent = 0.0
        order_count = 0
        if lead_phone or final_user_id:
            cond = []
            if lead_phone:
                cond.append(Order.customer_phone == lead_phone)
            if final_user_id:
                cond.append(Order.user_id == final_user_id)
            
            stmt = select(func.count(Order.id), func.sum(Order.total_amount)).where(
                and_(or_(*cond), Order.status == "DELIVERED")
            )
            agg_res = (await db.execute(stmt)).first()
            if agg_res:
                order_count = int(agg_res[0] or 0)
                total_spent = float(agg_res[1] or 0.0)

        dna = NeuralDNA(
            segment="VIP" if (order_count >= 3 or total_spent > 5000000) else ("REGULAR" if order_count >= 1 else "NEW"),
            vibe="WARM" if order_count >= 1 else "PROFESSIONAL",
            purchase_count=order_count,
            total_spent=total_spent,
            available_points=available_pts,
            point_value_vnd=pt_value,
            customer_name=customer_name
        )
        await xohi_memory.set_user_context(session_id, {"dna": dna.model_dump()})
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                _ttl = 300 if dna.segment == "VIP" else 600
                await xohi_memory.client.set(_dna_key, dna.model_dump_json(), ex=_ttl)
            except Exception as _se:
                logger.debug("[SupportAgent] DNA cache store failed: %s", _se)
        return dna
    except Exception as e:
        logger.warning("[SupportAgent] DNA fetch failed: %s", e)
        return NeuralDNA()

async def _prepare_pricing_breakdown(
    db: AsyncSession, request: SupportRequest, dna: NeuralDNA,
    p_map: Dict[str, ProductBase] | None = None,
    v_map: Dict[str, ProductVariant] | None = None,
) -> Dict[str, object]:
    if request.pricing_context and request.pricing_context.subtotal > 0:
        applied_vouchers = request.pricing_context.applied_voucher_ids or []
        if applied_vouchers:
            from sqlalchemy import select, and_, or_
            from datetime import datetime, timezone
            from backend.database.models.promotion import Voucher
            from backend.services.commerce.promotion import PromotionService
            from backend.services.commerce.logic.pricing_engine import PricingEngine
            from backend.schemas.pricing import PricingInputItem

            valid_vouchers = []
            now = datetime.now(timezone.utc)
            for v_id in applied_vouchers:
                stmt = select(Voucher).where(
                    Voucher.id == v_id,
                    Voucher.is_active == True,
                    Voucher.deleted_at.is_(None)
                )
                v_obj = (await db.execute(stmt)).scalar_one_or_none()
                if not v_obj:
                    continue
                if v_obj.start_date and v_obj.start_date > now:
                    continue
                if v_obj.end_date and v_obj.end_date < now:
                    continue
                
                # Check viral lock status
                if v_obj.is_viral:
                    from backend.services.viral_share_service import viral_share_service
                    is_unlocked = await viral_share_service.is_viral_unlocked(
                        user_id=request.user_id,
                        phone=request.customer_phone,
                        voucher_id=v_obj.id
                    )
                    if not is_unlocked:
                        logger.warning(f"[VOUCHER-VALIDATION] Filtered locked viral voucher {v_obj.id} for user={request.user_id}, phone={request.customer_phone}")
                        continue
                
                valid_vouchers.append(v_obj)
            
            # Recalculate using PricingEngine if any vouchers were filtered or to verify correctness
            _p_map = p_map or {}
            _v_map = v_map or {}
            input_items = []
            if request.cart_items:
                for it in request.cart_items:
                    p_raw = it.get("product", {})
                    v_raw = it.get("variant", {})
                    p_id = str(p_raw.get("id") or "")
                    if not p_id:
                        continue
                    p_db_item = _p_map.get(p_id)
                    v_db_item = _v_map.get(str(v_raw.get("id", ""))) if v_raw.get("id") else None
                    db_price = float(
                        v_db_item.price if v_db_item and v_db_item.price
                        else (p_db_item.price if p_db_item and p_db_item.price else 0)
                    )
                    if db_price <= 0:
                        continue
                    p_name = p_db_item.name if p_db_item else str(p_raw.get("name", "SP"))
                    input_items.append(PricingInputItem(
                        product_id=p_id, name=p_name,
                        quantity=int(it.get("quantity", 1) or 1),
                        unit_price=db_price
                    ))
            
            if input_items:
                combo_deals = await PromotionService.get_active_combo_deals(db)
                available_points = 0
                if request.user_id:
                    from backend.database.models.commerce import UserLoyalty
                    l_stmt = select(UserLoyalty.available_points).where(UserLoyalty.user_id == request.user_id)
                    available_points = (await db.execute(l_stmt)).scalar() or 0
                
                pb = PricingEngine.calculate(
                    items=input_items,
                    vouchers=valid_vouchers,
                    combo_deals=combo_deals,
                    points_to_redeem=request.pricing_context.points_redeemed or 0,
                    available_points=available_points,
                    base_shipping_fee=request.pricing_context.base_shipping_fee or 30000.0
                )
                res = pb.model_dump()
                res["is_fallback"] = False
                return res

        res = request.pricing_context.model_dump()
        res["is_fallback"] = False
        return res

    from backend.services.commerce.logic.pricing_engine import PricingEngine
    from backend.schemas.pricing import PricingInputItem
    _p_map = p_map or {}
    _v_map = v_map or {}
    input_items: list[PricingInputItem] = []
    if request.cart_items:
        for it in request.cart_items:
            p_raw = it.get("product", {})
            v_raw = it.get("variant", {})
            p_id = str(p_raw.get("id") or "")
            if not p_id:
                continue
            p_db_item = _p_map.get(p_id)
            v_db_item = _v_map.get(str(v_raw.get("id", ""))) if v_raw.get("id") else None
            db_price = float(
                v_db_item.price if v_db_item and v_db_item.price
                else (p_db_item.price if p_db_item and p_db_item.price else 0)
            )
            if db_price <= 0:
                continue
            p_name = p_db_item.name if p_db_item else str(p_raw.get("name", "SP"))
            input_items.append(PricingInputItem(
                product_id=p_id, name=p_name,
                quantity=int(it.get("quantity", 1) or 1),
                unit_price=db_price
            ))

    if not input_items:
        return {"subtotal": 0.0, "final_payable": 0.0, "is_fallback": True}
    pb = PricingEngine.calculate(input_items, base_shipping_fee=30000.0)
    res = pb.model_dump()
    res["is_fallback"] = True
    return res

async def _get_currency_settings() -> Dict[str, str]:
    try:
        async with xohi_memory.client.pipeline(transaction=False) as pipe:
            pipe.get("system:currency:symbol")
            pipe.get("system:currency:position")
            pipe.get("system:currency:thousand_sep")
            results = await pipe.execute()
        return {
            "symbol": str(results[0]) if results[0] else "₫",
            "position": str(results[1]) if results[1] else "suffix",
            "thousand_sep": str(results[2]) if results[2] else ".",
        }
    except Exception as e:
        logger.warning("[SupportAgent] Currency settings pipeline failed: %s", e)
        return {"symbol": "₫", "position": "suffix", "thousand_sep": "."}

def _format_price(amount: float, settings: Dict[str, str]) -> str:
    formatted = f"{int(amount):,}".replace(",", settings["thousand_sep"])
    if settings["position"] == "prefix":
        return f"{settings['symbol']}{formatted}"
    return f"{formatted}{settings['symbol']}"

def _trim_context_to_budget(
    cart_text: str, ctx_text: str, hist_text: str, kb_index: str,
    budget: int = 6000,
) -> tuple[str, str, str, str]:
    total = len(cart_text) + len(ctx_text) + len(hist_text) + len(kb_index)
    if total <= budget:
        return cart_text, ctx_text, hist_text, kb_index

    if len(hist_text) > 800:
        hist_text = hist_text[-800:]

    remaining = budget - len(cart_text) - len(ctx_text) - len(hist_text)
    if len(kb_index) > max(0, remaining):
        kb_index = kb_index[:max(0, remaining)] + "...[TRUNCATED]"

    remaining = budget - len(cart_text) - len(hist_text) - len(kb_index)
    if len(ctx_text) > max(0, remaining):
        ctx_text = ctx_text[:max(0, remaining)] + "...[TRUNCATED]"

    return cart_text, ctx_text, hist_text, kb_index

def _render_cart_report(
    request: SupportRequest, p_map: Dict[str, ProductBase],
    v_map: Dict[str, ProductVariant], pb: Dict[str, object], ctx_text: str,
    currency_settings: Dict[str, str]
) -> str:
    cart_lines = []
    if request.cart_items:
        for item in request.cart_items:
            p_raw = item.get("product", {})
            v_raw = item.get("variant", {})
            qty = item.get("quantity", 1)
            p_id = p_raw.get("id")
            if not p_id or p_id not in p_map:
                continue
            p_db = p_map[p_id]
            v_db = v_map.get(v_raw.get("id")) if v_raw.get("id") else None
            p_price = float(v_db.price if v_db else (p_db.price if p_db else (p_raw.get("price") or 0)))
            p_name = p_db.name
            v_label = v_raw.get("name") or v_raw.get("label")
            if v_label:
                p_name += f" ({v_label})"
            formatted_price = _format_price(p_price, currency_settings)
            formatted_total = _format_price(p_price * qty, currency_settings)
            cart_lines.append(f"- {p_name}: {qty} x {formatted_price} = {formatted_total}")

    current_product_text = f"\n[SẢN PHẨM KHÁCH ĐANG XEM TẠI TRANG HIỆN TẠI]:\n{ctx_text}\n" if request.product_slug and ctx_text else ""
    cart_lines_text = "\n".join(cart_lines) if cart_lines else "[GIỎ HÀNG THỰC]: Trống."
    cart_text = f"{current_product_text}\n[CHI TIẾT GIỎ HÀNG THỰC TẾ]\n{cart_lines_text}\n"
    
    if float(pb.get("subtotal", 0)) > 0:
        cart_text += f"\n[GIỎ HÀNG ĐIỆN TỬ - GROUND TRUTH]\n"
        if pb.get("is_fallback"):
            cart_text += "⚠️ [LƯU Ý]: Đang dùng logic dự phòng. Hãy nhắc khách kiểm tra lại tại Checkout.\n"
        cart_text += f"1. Tổng tạm tính: {_format_price(float(pb['subtotal']), currency_settings)}\n"
        if float(pb.get("combo_discount", 0.0)) > 0.0:
            cart_text += f"2. Chiết khấu Combo: -{_format_price(float(pb['combo_discount']), currency_settings)}\n"
        if float(pb.get("voucher_discount", 0.0)) > 0.0:
            applied_v = pb.get("applied_voucher_ids") or []
            v_label = f"(mã {', '.join(applied_v)})" if applied_v else ""
            cart_text += f"3. Giảm giá Voucher {v_label}: -{_format_price(float(pb['voucher_discount']), currency_settings)}\n"
        if float(pb.get("final_shipping_fee", 0.0)) > 0.0:
            cart_text += f"4. Phí vận chuyển: {_format_price(float(pb.get('base_shipping_fee', pb['final_shipping_fee'])), currency_settings)}\n"
            if float(pb.get("shipping_discount", 0.0)) > 0.0:
                cart_text += f"   - Đã giảm phí ship: -{_format_price(float(pb['shipping_discount']), currency_settings)}\n"
        else:
            cart_text += f"4. Phí vận chuyển: {_format_price(0.0, currency_settings)} (Miễn phí)\n"
        if float(pb.get("point_discount_amount", 0.0)) > 0.0:
            cart_text += f"5. Giảm giá điểm thưởng ({pb.get('points_redeemed', 0)} pts): -{_format_price(float(pb['point_discount_amount']), currency_settings)}\n"
        cart_text += f"\n👉 TỔNG THANH TOÁN CUỐI CÙNG: {_format_price(float(pb['final_payable']), currency_settings)}\n"
        cart_text += f"👉 DỰ KIẾN TÍCH LŨY: +{pb.get('points_to_earn', 0)} điểm.\n"
        cart_text += f"--------------------------------\n"
    return cart_text

def _generate_fomo_instructions(pb: Dict[str, object], all_vouchers: List[Voucher], currency_settings: Dict[str, str]) -> str:
    subtotal = float(pb.get("subtotal", 0))
    if subtotal <= 0:
        if not all_vouchers:
            return ""
        fomo_text = "\n[CHƯƠNG TRÌNH ƯU ĐÃI & VOUCHER ĐANG DIỄN RA (Hãy chủ động giới thiệu cho khách)]:\n"
        for v in all_vouchers:
            if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
                continue
            val_str = _format_price(float(v.value), currency_settings) if v.type != "PERCENT" else f"{v.value}%"
            min_str = f" (Đơn từ {_format_price(float(v.min_spend or 0.0), currency_settings)})" if v.min_spend else " (Mọi đơn hàng)"
            title_str = f" - {v.title}" if v.title else ""
            fomo_text += f"- Mã {v.id}: Giảm {val_str}{min_str}{title_str}\n"
        return fomo_text + "--------------------------------\n"
    best_v, max_sav = None, 0.0
    for v in all_vouchers:
        if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
            continue
        if subtotal < (v.min_spend or 0):
            continue
        sav = float(v.value) if v.type == "FIXED" else (subtotal * float(v.value) / 100 if v.type == "PERCENT" else 30000.0)
        if v.type == "PERCENT" and v.max_discount:
            sav = min(sav, float(v.max_discount))
        if sav > max_sav:
            max_sav, best_v = sav, v
    fomo_text = ""
    if best_v:
        fomo_text += f"\n[CHỈ THỊ FOMO CHO HELEN]:\n- Mã ưu đãi TỐT NHẤT hiện tại: '{best_v.id}' (Giảm ~{_format_price(max_sav, currency_settings)})\n"
        if float(pb.get("voucher_discount", 0)) < (max_sav - 1000):
            fomo_text += f"- [CẢNH BÁO]: Khách chưa dùng mã tốt nhất. HÃY THUYẾT PHỤC KHÁCH DÙNG MÃ '{best_v.id}'!\n"
        else:
            fomo_text += f"- [XÁC NHẬN]: Khách đã dùng mã tối ưu. Khen khách thông thái và chốt đơn ngay.\n"
    valid_vouchers = [v for v in all_vouchers if not (v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()))]
    next_v = next((v for v in sorted(valid_vouchers, key=lambda val: val.min_spend or 0) if (v.min_spend or 0) > subtotal), None)
    if next_v:
        gap = float(next_v.min_spend or 0.0) - subtotal
        if gap < 300000:
            fomo_text += f"- Gợi ý mua thêm: Chỉ thiếu {_format_price(gap, currency_settings)} nữa là dùng được mã '{next_v.id}' (Giảm cực sâu).\n"
    return fomo_text + "--------------------------------\n" if fomo_text else ""

async def _try_db_first_fast_path(
    db: AsyncSession, request: SupportRequest, p_info: Optional[SupportProductInfo],
    c_name: str, cur_settings: Dict[str, str], ctx_text: str
) -> Optional[SupportResponse]:
    if not p_info:
        return None
    
    msg_norm = request.message.lower().strip()
    p_name = p_info.name
    price_display = p_info.price_display or f"{int(p_info.price):,}đ".replace(",", ".")
    
    stmt = select(ProductBase.product_metadata).where(
        ProductBase.id == p_info.id,
        ProductBase.deleted_at.is_(None)
    )
    meta_res = await db.execute(stmt)
    product_meta = meta_res.scalar_one_or_none() or {}

    benefit_lines: list[str] = []
    section_label = "Công dụng nổi bật của sản phẩm:"
    if isinstance(product_meta, dict):
        fi_list = product_meta.get("featured_ingredients")
        if isinstance(fi_list, list) and fi_list:
            for fi in fi_list:
                fi_icon = fi.get("icon", "🧬")
                fi_name = fi.get("name", "")
                fi_benefit = fi.get("benefit", "")
                if fi_name:
                    fi_name_safe = re.sub(r'<[^>]+>', ' ', str(fi_name))[:80].strip()
                    fi_benefit_safe = re.sub(r'<[^>]+>', ' ', str(fi_benefit))[:200].strip()
                    benefit_lines.append(f"{fi_icon} {fi_benefit_safe}" if fi_benefit_safe else f"{fi_icon} {fi_name_safe}")

        if not benefit_lines:
            ki_list = product_meta.get("key_ingredients")
            if isinstance(ki_list, list):
                for ki in ki_list:
                    k_name = ki.get("name")
                    k_desc = ki.get("description")
                    if k_name:
                        k_name_safe = re.sub(r'<[^>]+>', ' ', str(k_name))[:80].strip()
                        k_desc_safe = re.sub(r'<[^>]+>', ' ', str(k_desc))[:200].strip() if k_desc else ""
                        benefit_lines.append(f"🧬 {k_desc_safe}" if k_desc_safe else f"🧬 {k_name_safe}")

        if not benefit_lines:
            ingredients_str = product_meta.get("ingredients")
            if isinstance(ingredients_str, str) and ingredients_str.strip():
                section_label = "Thành phần nổi bật:"
                clean_ings = re.sub(r'<[^>]+>', ' ', ingredients_str).strip()
                ings = [i.strip() for i in re.split(r'[,;]', clean_ings) if i.strip()]
                for ing in ings[:4]:
                    benefit_lines.append(f"🧬 {ing}")

    if not benefit_lines and ctx_text:
        in_ing_section = False
        for line in ctx_text.split("\n"):
            line_strip = line.strip()
            if "[THÀNH PHẦN NỔI BẬT & CÔNG DỤNG]" in line_strip or "[BẢNG THÀNH PHẦN CHI TIẾT]" in line_strip:
                in_ing_section = True
                continue
            if in_ing_section and line_strip.startswith("["):
                in_ing_section = False
            if in_ing_section and line_strip:
                cleaned = line_strip.lstrip("- ").strip()
                if cleaned:
                    benefit_lines.append(f"🧬 {cleaned}")

    db_first_reply = None
    if "[system_consult]" in msg_norm:
        benefit_text = "\n".join(benefit_lines[:4]) if benefit_lines else "🧬 Chiết xuất thảo dược tự nhiên chuẩn Nhật Bản."
        db_first_reply = (
            f"Dạ Helen chào Anh/Chị! Rất vui được tư vấn liệu trình chăm sóc da hoàn hảo với {p_name} ạ! ✨\n\n"
            f"🌸 {section_label}\n"
            f"{benefit_text}\n\n"
            f"💰 Giá ưu đãi độc quyền: {price_display}\n\n"
            f"💬 Để nhận quà tặng độc quyền kèm đơn hàng hôm nay, Anh/Chị nhắn ngay Số Điện Thoại + Địa Chỉ để Helen lên đơn giao tận nơi nhé! 🌸"
        )
    elif "[system_skin_barrier]" in msg_norm or "an toàn da" in msg_norm:
        ingredients_raw = ""
        if isinstance(product_meta, dict):
            ingredients_raw = str(product_meta.get("ingredients", "")).lower()
        
        safety_claims: list[str] = []
        if not any(kw in ingredients_raw for kw in ["alcohol", "ethanol", "cồn", "denat"]):
            safety_claims.append("không chứa cồn")
        if not any(kw in ingredients_raw for kw in ["paraben", "methylparaben", "propylparaben"]):
            safety_claims.append("không paraben")
        if not any(kw in ingredients_raw for kw in ["fragrance", "parfum", "hương liệu"]):
            safety_claims.append("không hương liệu tổng hợp")
        
        safety_line = f"• {', '.join(safety_claims).capitalize()}.\n" if safety_claims else "• Thành phần được kiểm nghiệm nghiêm ngặt theo tiêu chuẩn an toàn.\n"
        
        cert_line = "• Đầy đủ kiểm nghiệm và chứng nhận từ cơ quan quản lý.\n"
        if ctx_text and "Hồ sơ pháp lý:" in ctx_text:
            for line in ctx_text.split("\n"):
                if "Hồ sơ pháp lý:" in line:
                    cert_info = line.strip().replace("- ", "").replace("Hồ sơ pháp lý: ", "")
                    if cert_info and cert_info != "Chưa có chứng nhận":
                        cert_line = f"• Hồ sơ pháp lý: {cert_info}.\n"
                    break
        
        db_first_reply = (
            f"Dạ Anh/Chị hoàn toàn yên tâm nhé! Siêu phẩm **{p_name}** được bào chế chuẩn y khoa, cam kết:\n"
            f"{safety_line}"
            f"• Phù hợp cho nhiều loại da, kể cả da nhạy cảm.\n"
            f"{cert_line}\n"
            f"Anh/Chị cần Helen tư vấn kỹ hơn về cách kết hợp sản phẩm vào chu trình dưỡng da hiện tại không ạ? 🌸"
        )
    elif "xuất xứ" in msg_norm or "nguồn gốc" in msg_norm:
        origin_line = "Chính hãng nhập khẩu nguyên kiện."
        cert_line_origin = ""
        if ctx_text:
            for line in ctx_text.split("\n"):
                if "Xuất xứ:" in line:
                    origin_line = line.strip().replace("- ", "• ")
                elif "Hồ sơ pháp lý:" in line:
                    cert_line_origin = "\n" + line.strip().replace("- ", "• ")
        
        origin_country = "chính hãng"
        if isinstance(product_meta, dict) and product_meta.get("origin"):
            origin_country = str(product_meta["origin"])
        elif ctx_text:
            for line in ctx_text.split("\n"):
                if "Xuất xứ:" in line:
                    origin_country = line.strip().replace("- Xuất xứ: ", "").strip()
                    break
        
        db_first_reply = (
            f"Dạ để Anh/Chị an tâm tuyệt đối, đây là nguồn gốc xuất xứ chính thức của **{p_name}** ạ! 🛡️\n\n"
            f"{origin_line}{cert_line_origin}\n\n"
            f"Sản phẩm nhập khẩu chính ngạch từ {origin_country}, đầy đủ hóa đơn đỏ, hóa đơn VAT và tem chống hàng giả nên mình hoàn toàn yên tâm khi sử dụng ạ. 🌸"
        )
    elif "công dụng" in msg_norm or "thành phần" in msg_norm:
        benefit_text_4 = "\n".join(benefit_lines[:6]) if benefit_lines else "🧬 Chứa các dưỡng chất tự nhiên cao cấp củng cố hàng rào bảo vệ da, giúp da căng bóng, mịn màng và trắng sáng khỏe mạnh."
        db_first_reply = (
            f"Dạ gửi Anh/Chị thông tin chi tiết về thành phần & công dụng của {p_name} ạ! ✨\n\n"
            f"{benefit_text_4}\n\n"
            f"Anh/Chị nhắn lại tình trạng da hiện tại (da khô, dầu, mụn...) để Helen hướng dẫn cách sử dụng đạt hiệu quả tốt nhất nhé! 🌸"
        )

    if db_first_reply:
        from backend.services.commerce.operatives.utils import _sanitize_response
        safe_reply = _sanitize_response(db_first_reply)
        return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PRODUCT_QUERY, session_id=request.session_id, product_info=p_info, status="DONE")
    return None
