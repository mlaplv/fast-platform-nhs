"""
Sync Order Heuristics & Slot Fill Helpers — SUPPORT_NAME_CLIENT (Architect's Edition)
====================================================================================
Elite V5.5: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations
import json
import logging
import os
import re
from typing import Optional, List, Dict, TYPE_CHECKING
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.support import SupportRequest, SupportResponse, SupportIntent, SupportProductInfo
from backend.schemas.order import OrderDraft
from backend.database.models.promotion import Voucher
from backend.services.commerce.promotion import PromotionService
from backend.services.xohi_memory import xohi_memory
from backend.services.commerce.operatives.utils import _sanitize_response

if TYPE_CHECKING:
    from backend.services.commerce.operatives.support_agent import SupportAgentOperative

logger = logging.getLogger("arq.worker")

async def _try_heuristic_sync(
    agent: SupportAgentOperative, request: SupportRequest, db: AsyncSession,
    session_id: str, p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None
) -> Optional[SupportResponse]:
    """Bypass LLM reasoning for common policy/address/hotline questions."""
    msg_norm = request.message.lower().strip()
    if any(kw in msg_norm for kw in ["thành phần", "chiết xuất", "ship", "phí", "nguồn gốc", "xuất xứ", "chính hãng", "uy tín", "giấy phép", "pháp lý"]):
        return None
    cur_settings = await agent._get_currency_settings()
    if any(kw in msg_norm for kw in ["giá", "bao nhiêu"]) and p_info and not request.cart_items:
        final_reply = f"Dạ liệu trình **{p_info.name}** giá từ **{p_info.price_display}** ạ. 🌸"
        await agent._save_history(db, session_id, request.message, final_reply, SupportIntent.PRICE_QUERY, request.product_slug, customer_name)
        await agent._emit_inbox_update(session_id, request.message)
        return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.PRICE_QUERY, session_id=session_id, status="DONE")
    
    is_address = any(kw in msg_norm for kw in ["địa chỉ", "ở đâu"])
    is_hotline = any(kw in msg_norm for kw in ["điện thoại", "hotline"])
    if is_address or is_hotline:
        raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
        if not raw_cfg: return None
        ci = json.loads(raw_cfg).get("contact_info", {})
        final_reply = f"Dạ địa chỉ: **{ci.get('address')}** ạ. 🌸" if is_address else f"Hotline: **{ci.get('hotline')}** ạ. 🌸"
        await agent._save_history(db, session_id, request.message, final_reply, SupportIntent.POLICY_QUERY, request.product_slug, customer_name)
        await agent._emit_inbox_update(session_id, request.message)
        return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.POLICY_QUERY, session_id=session_id, status="DONE")
    return None

async def _try_sync_order_fast_path(
    agent: SupportAgentOperative, request: SupportRequest, db: AsyncSession,
    session_id: str, p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None
) -> Optional[SupportResponse]:
    """Elite V7.1 Fast-Path Order Creation."""
    if not p_info: return None
    msg = request.message.lower().strip()
    if msg.startswith("[system_") or "?" in msg: return None

    import unicodedata
    msg_nfkc = unicodedata.normalize("NFKC", msg)
    buy_kws = ["cho", "mua", "đặt", "lấy", "gửi", "ship"]
    unit_kws = ["hộp", "lọ", "chai", "cái", "bộ", "set", "tuýp", "gói", "túi", "sp", "sản phẩm"]
    if not (any(kw in msg_nfkc for kw in buy_kws) and any(kw in msg_nfkc for kw in unit_kws) and len(msg) < 40):
        return None

    qty_match = re.search(r"(\d+)", msg_nfkc)
    quantity = int(qty_match.group(1)) if qty_match else 1
    if quantity < 1 or quantity > 100: return None

    logger.info(f"⚡ [SyncOrderFastPath] Detected purchase: '{msg}' → {p_info.name} x{quantity}")
    unit_price = float(p_info.price or 0)
    if unit_price <= 0: return None

    from backend.services.commerce.logic.lead_extractor import LeadExtractor
    from backend.database import current_tenant_id
    tid = current_tenant_id.get() or "default"
    resolved_product = await LeadExtractor._resolve_product(db, name=p_info.name, slug=p_info.slug, tenant_id=tid)

    actual_price = unit_price
    actual_qty = quantity
    gift_lines: List[str] = []
    gift_list: List[dict] = []
    variant_sku = ""
    if resolved_product:
        best_variant, protocol_qty, _ = LeadExtractor._resolve_optimal_variant(resolved_product, quantity)
        if best_variant:
            actual_price = float(best_variant.discount_price or best_variant.price)
            actual_qty = protocol_qty
            variant_sku = best_variant.sku or ""
            v_attrs = best_variant.attributes or {}
            if isinstance(v_attrs, str):
                try: v_attrs = json.loads(v_attrs)
                except Exception: v_attrs = {}
            if isinstance(v_attrs, dict):
                gift_list = v_attrs.get("gifts") or []
                for g in gift_list:
                    if isinstance(g, dict) and g.get("name"):
                        gift_lines.append(f"🎁 + {g['name']} (x{g.get('qty', 1)})")

    subtotal = actual_price * actual_qty

    # Upsell Suggestion
    upsell_line = ""
    if resolved_product and resolved_product.variants:
        for v in resolved_product.variants:
            v_attrs = v.attributes or {}
            if isinstance(v_attrs, str):
                try: v_attrs = json.loads(v_attrs)
                except Exception: v_attrs = {}
            v_combo_qty = int(v_attrs.get('combo_qty') or v_attrs.get('comboQty') or 1)
            v_gifts = v_attrs.get('gifts') or []
            v_total = v_combo_qty + sum(int(g.get('qty', 0)) for g in v_gifts if isinstance(g, dict))
            extra_needed = v_combo_qty - actual_qty
            if extra_needed > 0 and extra_needed <= 2 and v_total > (actual_qty + len(gift_lines)):
                upsell_price = float(v.discount_price or v.price)
                upsell_formatted = "{:,.0f}".format(upsell_price).replace(",", ".")
                gift_names = [g.get("name", "") for g in v_gifts if isinstance(g, dict) and g.get("name")]
                gift_text = f" + tặng **{', '.join(gift_names)}**" if gift_names else ""
                
                dna_temp = await agent._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
                c_display_temp = dna_temp.customer_name or customer_name or "mình"
                if c_display_temp in ["Khách ẩn danh", "Quý khách", "Sếp"]: c_display_temp = "mình"
                    
                upsell_line = (
                    f"💡 Mua thêm **{extra_needed}** = **{v_combo_qty} hộp** giá chỉ **{upsell_formatted}đ**{gift_text}! "
                    f"Tiết kiệm hơn nhiều — {c_display_temp} có muốn nâng lên không ạ?"
                )
                break

    # Voucher query
    from datetime import datetime, timezone as tz
    now = datetime.now(tz.utc)
    v_stmt = select(Voucher).where(
        and_(
            Voucher.deleted_at.is_(None),
            Voucher.is_active == True,
            or_(Voucher.is_viral == False, Voucher.is_viral.is_(None)),
            Voucher.tenant_id == tid,
            or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
            or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
            Voucher.min_spend <= subtotal,
        )
    ).order_by(Voucher.priority.desc(), Voucher.value.desc()).limit(5)
    voucher_rows = (await db.execute(v_stmt)).scalars().all()

    best_voucher = None
    best_voucher_discount = 0.0
    has_free_ship_voucher = False
    for v in voucher_rows:
        if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
            continue
        if v.type == "SHIPPING" or v.category == "SHIPPING":
            has_free_ship_voucher = True
            continue
        disc = PromotionService.calculate_voucher_discount(subtotal, v)
        if disc > best_voucher_discount:
            best_voucher_discount = disc
            best_voucher = v

    dna = await agent._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
    c_display = dna.customer_name or customer_name
    if not c_display or c_display in ["Khách ẩn danh", "Quý khách", "Sếp"]: c_display = "mình"

    pts_discount = 0.0
    if dna.available_points > 0 and dna.point_value_vnd > 0:
        pts_discount = min(dna.available_points * dna.point_value_vnd, subtotal * 0.3)

    final_price = subtotal - best_voucher_discount - pts_discount
    if final_price < 0: final_price = 0.0

    p_name_full = resolved_product.name if resolved_product else p_info.name
    draft_item = {
        "product_id": p_info.id,
        "id": p_info.slug,
        "name": f"{p_name_full} ({variant_sku})" if variant_sku else p_name_full,
        "price": actual_price,
        "quantity": actual_qty,
        "gifts": gift_list,
    }

    draft = OrderDraft(
        session_id=session_id, items=[draft_item],
        customer_name=c_display if c_display != "mình" else None, is_definite_intent=True,
    )
    await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))

    p_name_short = p_name_full.split(" - ")[0] if " - " in p_name_full else p_name_full
    if len(p_name_short) > 50: p_name_short = p_name_short[:50] + "..."

    formatted_subtotal = "{:,.0f}".format(subtotal).replace(",", ".")
    formatted_final = "{:,.0f}".format(final_price).replace(",", ".")
    debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""
    ship_text = "free ship" if has_free_ship_voucher else ""

    reply_parts = [f"{debug_prefix}Dạ Helen nhận đơn **{actual_qty} {p_name_short}** cho {c_display} rồi ạ! 🌸\n"]
    if gift_lines:
        reply_parts.append("🎉 **Ưu đãi combo:**")
        reply_parts.extend(gift_lines)
        reply_parts.append("")

    reply_parts.append(f"💰 Giá: **{formatted_subtotal}đ**")
    if best_voucher and best_voucher_discount > 0:
        v_display = "{:,.0f}".format(best_voucher_discount).replace(",", ".")
        reply_parts.append(f"🏷️ Mã **{best_voucher.id}**: giảm **{v_display}đ** ({int(best_voucher.value)}%)" if best_voucher.type == "PERCENT" else f"🏷️ Mã **{best_voucher.id}**: giảm **{v_display}đ**")

    if dna.available_points > 0 and pts_discount > 0:
        pts_display = "{:,.0f}".format(pts_discount).replace(",", ".")
        reply_parts.append(f"⭐ Đổi **{dna.available_points} điểm** → giảm thêm **{pts_display}đ**")

    ship_suffix = f" ({ship_text})" if ship_text else ""
    reply_parts.append(f"✅ **Tổng thanh toán: {formatted_final}đ**{ship_suffix}" if (best_voucher_discount > 0 or pts_discount > 0) else f"✅ **Tổng: {formatted_subtotal}đ**{ship_suffix}")
    if upsell_line: reply_parts.append(f"\n{upsell_line}")
    if dna.segment == "VIP": reply_parts.append(f"\n💎 Cảm ơn {c_display} — khách VIP thân thiết của osmo! Helen sẽ ưu tiên giao nhanh nhất cho {c_display} ạ.")
    reply_parts.append(f"\n{c_display.capitalize()} cho em xin nhanh:\n📞 **Số điện thoại**\n📍 **Địa chỉ nhận hàng**\nđể em lên bill giao tận nơi luôn nhé! ✨")

    reply = "\n".join(reply_parts)
    safe_reply = _sanitize_response(reply)
    await agent._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
    await agent._emit_inbox_update(session_id, request.message)
    await db.flush()
    return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, product_info=p_info, status="DONE")

async def _try_sync_slot_fill(
    agent: SupportAgentOperative, request: SupportRequest, db: AsyncSession,
    session_id: str, draft: OrderDraft, customer_name: Optional[str] = None
) -> Optional[SupportResponse]:
    """Elite V7.0 Sync Slot Filler."""
    msg = request.message.strip()
    digits_only = re.sub(r"\D", "", msg)

    extracted_phone = None
    if len(digits_only) >= 9 and len(digits_only) <= 12:
        extracted_phone = digits_only
    else:
        phone_match = re.search(r"\b(0\d{9})\b", msg)
        if phone_match: extracted_phone = phone_match.group(1)

    has_addr_signal = "/" in msg or any(
        kw in msg.lower() for kw in [
            "đường", "phố", "phường", "quận", "huyện", "xã", "tỉnh",
            "tp", "thành phố", "số", "ngõ", "ngách", "p.", "q."
        ]
    )
    digit_ratio = len(digits_only) / len(msg) if msg else 0.0
    extracted_address = None
    if has_addr_signal or (len(msg) > 15 and digit_ratio < 0.5):
        addr_text = msg
        if extracted_phone and extracted_phone in digits_only:
            addr_text = re.sub(r"0\d{9}", "", msg).strip().strip(",").strip()
        if len(addr_text) > 5: extracted_address = addr_text

    filled_something = False
    if extracted_phone and not draft.customer_phone:
        from backend.services.commerce.logic.lead_extractor import validate_vietnam_phone
        validated = validate_vietnam_phone(extracted_phone)
        if validated:
            draft.customer_phone = validated
            filled_something = True

    if extracted_address and not draft.customer_address:
        draft.customer_address = extracted_address
        filled_something = True

    if not filled_something: return None
    await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))

    debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""
    dna = await agent._fetch_neural_dna(db, session_id, lead_phone=draft.customer_phone, user_id=request.user_id)
    c_display = dna.customer_name or customer_name
    if not c_display or c_display in ["Khách ẩn danh", "Quý khách", "Sếp"]: c_display = "mình"

    if draft.is_complete:
        from backend.services.commerce.logic.location_resolver import location_resolver
        shipping_days = "3-5 ngày"
        try:
            import asyncio as _asyncio
            geo = await _asyncio.to_thread(location_resolver.resolve, draft.customer_address)
            if geo.is_valid:
                shipping_days = geo.shipping_days or shipping_days
                if geo.province and geo.province not in (draft.customer_address or ""):
                    draft.customer_address = f"{draft.customer_address}, {geo.province}"
            elif geo.possible_provinces:
                provinces = ", ".join(geo.possible_provinces)
                await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))
                reply = f"{debug_prefix}Dạ địa chỉ của {c_display} trùng tên ở nhiều nơi ({provinces}), {c_display} cho Helen xin thêm Tỉnh/Thành phố nhé! 🌸"
                safe_reply = _sanitize_response(reply)
                await agent._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
                await agent._emit_inbox_update(session_id, request.message)
                await db.flush()
                return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")
        except Exception as geo_err:
            logger.warning(f"[SyncSlotFill] Geo resolution failed: {geo_err}")

        try:
            from backend.services.commerce.order import OrderService
            from backend.schemas.order import OrderCreateRequest
            from backend.database import current_tenant_id
            from backend.services.user_service import user_service
            tid = current_tenant_id.get() or "default"
            resolved_user = None
            if draft.customer_phone:
                resolved_user, _, _, _ = await user_service.get_or_resolve_customer(
                    db=db, phone=draft.customer_phone,
                    name=draft.customer_name or customer_name, 
                    current_address=draft.customer_address, tenant_id=tid
                )
            user_id = str(resolved_user.id) if resolved_user else "guest"

            from backend.services.commerce.logic.lead_extractor import LeadExtractor
            enriched_items = []
            for it in draft.items:
                enriched_item = dict(it)
                enriched_item.setdefault("id", enriched_item.get("product_id", ""))
                enriched_item.setdefault("product_id", enriched_item.get("id", ""))
                enriched_item.setdefault("quantity", enriched_item.get("qty", 1))
                enriched_item.setdefault("unit_price", enriched_item.get("price", 0))
                
                # Dynamic fallback gift resolution if gifts is missing/empty
                if not enriched_item.get("gifts"):
                    resolved_p = await LeadExtractor._resolve_product(
                        db, name=enriched_item.get("name"),
                        slug=enriched_item.get("id"), tenant_id=tid
                    )
                    if resolved_p:
                        best_v, _, _ = LeadExtractor._resolve_optimal_variant(resolved_p, int(enriched_item["quantity"]))
                        if best_v:
                            v_attrs = best_v.attributes or {}
                            if isinstance(v_attrs, str):
                                try:
                                    v_attrs = json.loads(v_attrs)
                                except Exception:
                                    v_attrs = {}
                            if isinstance(v_attrs, dict):
                                enriched_item["gifts"] = v_attrs.get("gifts") or []
                
                enriched_items.append(enriched_item)

            subtotal = sum(float(it.get("price") or it.get("unit_price") or 0.0) * int(it.get("quantity") or it.get("qty") or 1) for it in enriched_items)

            # Query best voucher
            from datetime import datetime, timezone as tz
            now = datetime.now(tz.utc)
            v_stmt = select(Voucher).where(
                and_(
                    Voucher.deleted_at.is_(None),
                    Voucher.is_active == True,
                    or_(Voucher.is_viral == False, Voucher.is_viral.is_(None)),
                    Voucher.tenant_id == tid,
                    or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                    or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
                    Voucher.min_spend <= subtotal,
                )
            ).order_by(Voucher.priority.desc(), Voucher.value.desc()).limit(5)
            voucher_rows = (await db.execute(v_stmt)).scalars().all()

            best_voucher = None
            best_voucher_discount = 0.0
            has_free_ship_voucher = False
            for v in voucher_rows:
                if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
                    continue
                if v.type == "SHIPPING" or v.category == "SHIPPING":
                    has_free_ship_voucher = True
                    continue
                disc = PromotionService.calculate_voucher_discount(subtotal, v)
                if disc > best_voucher_discount:
                    best_voucher_discount = disc
                    best_voucher = v

            pts_discount = 0.0
            if dna.available_points > 0 and dna.point_value_vnd > 0:
                pts_discount = min(dna.available_points * dna.point_value_vnd, subtotal * 0.3)

            total = subtotal - best_voucher_discount - pts_discount
            if total < 0: total = 0.0

            order_data = OrderCreateRequest(
                items=enriched_items, total_amount=max(total, subtotal * 0.3),
                customer_name=dna.customer_name or draft.customer_name or customer_name or "Quý khách",
                customer_email=f"{draft.customer_phone}@helen.osmo.vn", customer_phone=draft.customer_phone,
                customer_address=draft.customer_address,
            )

            result = await OrderService.create_order(db, order_data, ip="0.0.0.0", ua="Helen-SyncFastPath", user_id=user_id)
            order_id = result.id
            await xohi_memory.clear_order_draft(session_id)

            formatted_subtotal = "{:,.0f}".format(subtotal).replace(",", ".")
            formatted_total = "{:,.0f}".format(total).replace(",", ".")
            ship_text = "free ship" if has_free_ship_voucher else ""

            reply_parts = [
                f"{debug_prefix}Dạ Helen chúc mừng {c_display} đặt hàng thành công! 🌸\n",
                f"📋 **CHI TIẾT ĐƠN HÀNG**",
                f"🆔 Mã đơn: **{order_id[-8:].upper()}**",
            ]

            for it in enriched_items:
                name = str(it.get("name", "SP"))
                qty = int(it.get("quantity") or it.get("qty") or 1)
                reply_parts.append(f"📦 {name} (x{qty})")
                gifts = it.get("gifts") or []
                if gifts:
                    gift_strs = [f"{g.get('name', 'SP')} (x{g.get('qty', 1)})" for g in gifts if isinstance(g, dict)]
                    if gift_strs: reply_parts.append(f"   🎁 + {', '.join(gift_strs)}")

            has_discount = best_voucher_discount > 0 or pts_discount > 0
            ship_suffix = f" ({ship_text})" if ship_text else ""
            if has_discount:
                reply_parts.append(f"💰 Giá gốc: ~~{formatted_subtotal}đ~~")
                if best_voucher and best_voucher_discount > 0:
                    v_display = "{:,.0f}".format(best_voucher_discount).replace(",", ".")
                    reply_parts.append(f"🏷️ Mã {best_voucher.id}: −{v_display}đ")
                if dna.available_points > 0 and pts_discount > 0:
                    pts_display = "{:,.0f}".format(pts_discount).replace(",", ".")
                    reply_parts.append(f"⭐ Đổi {dna.available_points} điểm: −{pts_display}đ")
                reply_parts.append(f"✅ **Thanh toán: {formatted_total}đ**{ship_suffix}")
            else:
                reply_parts.append(f"💰 **Tổng: {formatted_subtotal}đ**{ship_suffix}")

            reply_parts.append(f"🚚 Dự kiến: **{shipping_days}**")
            if dna.segment == "VIP": reply_parts.append(f"\n💎 Khách VIP — Helen ưu tiên giao nhanh cho {c_display} ạ!")
            reply_parts.append(f"\n{c_display.capitalize()} nhớ để ý điện thoại khi shipper gọi nha! 📞\nCảm ơn {c_display} đã tin tưởng osmo! 💖")

            reply = "\n".join(reply_parts)
            safe_reply = _sanitize_response(reply)
            await agent._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
            await agent._emit_inbox_update(session_id, request.message)
            await db.flush()
            logger.info(f"⚡ [SyncSlotFill] Order created: {order_id}")
            return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")

        except Exception as order_err:
            logger.error(f"[SyncSlotFill] Order creation failed: {order_err}")
            return None

    # Draft incomplete
    missing = draft.missing_slots
    item_names = ", ".join([f"{it.get('name', 'SP')} x{it.get('quantity', 1)}" for it in draft.items])
    reply = (
        f"{debug_prefix}Dạ Helen đã ghi nhận thông tin {', '.join([f'{k}: **{v}**' for k, v in [('SĐT', draft.customer_phone), ('Địa chỉ', draft.customer_address)] if v])} "
        f"cho đơn hàng{item_names} rồi ạ! 🌸\n\n"
        f"Helen còn thiếu {', '.join([f'**{m}**' for m in missing])}, {c_display} nhắn nhanh nốt để em gửi hàng đi luôn nhé! ✨"
    )
    safe_reply = _sanitize_response(reply)
    await agent._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
    await agent._emit_inbox_update(session_id, request.message)
    await db.flush()
    return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")
