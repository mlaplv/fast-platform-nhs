from __future__ import annotations
import logging
import unicodedata
from sqlalchemy import select
from backend.database.models.commerce import Order
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.services.commerce.logic.lead_extractor import lead_extractor, ExtractedLead, LeadOrderItem, validate_vietnam_phone
from backend.services.commerce.logic.location_resolver import location_resolver
from backend.services.xohi_memory import xohi_memory
from backend.schemas.support import SupportIntent
from backend.schemas.order import OrderDraft

logger = logging.getLogger("api-gateway")

class OrderHandler(BaseHandler):
    """
    ZONE 3: The Order Closer and Status Specialist.
    Priority: Identify purchase intent and extract leads.
    """
    
    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 3: Order Closing. Refined Elite V3.0 Architecture."""
        msg = unicodedata.normalize("NFKC", ctx.request.message.lower().strip())
        session_id = ctx.session_id
        logger.info(f"⚡ [OrderHandler] Checking Intent for SID: {session_id} | Msg: '{msg[:30]}...' | HasDraft: {bool(ctx.order_draft)}")
        
        import os
        import re
        from backend.database.models.promotion import Voucher
        from sqlalchemy import and_, or_
        from datetime import datetime, timezone
        
        debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""

        # --- Q1: KIỂM TRA TRẠNG THÁI & HỦY ĐƠN (ORDER_STATUS / CANCEL) ---
        check_patterns = ["check đơn", "đơn tới đâu", "vận đơn", "đơn của chị", "bao giờ nhận", "trạng thái đơn"]
        cancel_patterns = ["hủy đơn", "không mua nữa", "hủy cho chị", "bỏ đơn"]
        
        is_check = any(p in msg for p in check_patterns)
        is_cancel = any(p in msg for p in cancel_patterns)
        
        if is_check or is_cancel:
            ctx.intent = SupportIntent.ESCALATE if is_cancel else SupportIntent.ORDER_STATUS # Mapping intent cho hệ thống
            phone_to_check = ctx.lead_data.customer_phone if ctx.lead_data else None
            if not phone_to_check:
                match = re.search(r"(0\d{9})", msg)
                if match: phone_to_check = match.group(1)
            
            if not phone_to_check:
                ctx.replies.append(f"{debug_prefix}Dạ để kiểm tra đơn hàng, Anh/Chị cho Helen xin **Số điện thoại** lúc đặt hàng nhé! 🌸")
                return True
                
            recent_order = (await ctx.db.execute(select(Order).where(Order.customer_phone == phone_to_check).order_by(Order.created_at.desc()).limit(1))).scalar_one_or_none()
            
            masked_phone = f"{phone_to_check[:3]}****{phone_to_check[-3:]}"
            
            if not recent_order:
                ctx.replies.append(f"{debug_prefix}Dạ Helen không tìm thấy đơn hàng nào gần đây của SĐT {masked_phone} ạ. Anh/Chị kiểm tra lại số điện thoại giúp em nhé! 🌸")
                return True

            if is_cancel:
                if recent_order.status in ["PENDING", "DRAFT"]:
                    recent_order.status = "CANCELLED"
                    await ctx.db.flush()
                    ctx.replies.append(f"{debug_prefix}Dạ Helen đã ghi nhận **Hủy đơn hàng** của SĐT {masked_phone} thành công rồi ạ. Hẹn sớm được phục vụ mình trong lần tới nhé! 🌸")
                else:
                    ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} hiện đang ở trạng thái **{recent_order.status}** và đã được giao cho Shipper, nên Helen không tự động hủy được nữa ạ. Anh/Chị vui lòng từ chối nhận hàng khi shipper gọi nha! 🌸")
                return True

            # Tracking Info
            if recent_order.status == "PENDING":
                ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} hiện đang **Chờ đóng gói** và sẽ được gửi đi trong hôm nay ạ. Anh/Chị chú ý điện thoại nha! 🌸")
            elif recent_order.status == "SHIPPING":
                ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} hiện **Đang trên đường giao**. Dự kiến 1-2 ngày tới shipper sẽ gọi, Anh/Chị để ý điện thoại nha! 🌸")
            elif recent_order.status == "COMPLETED":
                ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} đã **Giao thành công** rồi ạ. Cảm ơn Anh/Chị đã luôn tin tưởng và đồng hành cùng Micsmo! ✨")
            elif recent_order.status == "CANCELLED":
                ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} đã bị **Hủy** trước đó rồi ạ. Nếu cần mua lại, Anh/Chị cứ báo em nhé! 🌸")
            else:
                ctx.replies.append(f"{debug_prefix}Dạ đơn hàng của SĐT {masked_phone} hiện ở trạng thái **{recent_order.status}**. Anh/Chị chờ thêm chút nữa nhé! 🌸")
            return True


        # --- Q2: TẠO ĐƠN & VOUCHER INTELLIGENCE (PURCHASE) ---
        staff_patterns = ["cho 1 đơn", "cho đơn", "về :", "về:", "lên đơn", "gửi đơn"]
        potential_keywords = ["mua", "đặt", "lấy", "ship", "giao", "ok", "chốt", "đơn", "cho"]

        has_digits = any(char.isdigit() for char in msg)
        # Elite V3.6: Loose phone check (9-11 digits) to catch typos
        has_standalone_phone = bool(re.search(r"0\d{8,10}", msg))
        is_staff_order = any(sp in msg for sp in staff_patterns) and has_digits
        has_buying_intent = any(kw in msg for kw in potential_keywords)
        
        # Elite V3.6: Trigger if there's buying intent OR a standalone phone OR active draft exists (Sticky)
        is_strong_intent = has_digits and (has_buying_intent or is_staff_order or has_standalone_phone)
        
        # 🚀 V4.1: Sticky Order Protocol
        # If we have an active draft, OR the message is a clear phone/address after a purchase prompt,
        # we MUST hold the intent to prevent falling through to ConsultantHandler for slot-filling.
        if ctx.order_draft:
            logger.info(f"🎯 [OrderHandler] Sticky Check: Active Draft found for SID {session_id}")
            # Only sticky if it looks like they are providing the missing info (digits = phone/address, / = address)
            if has_digits or has_standalone_phone or "/" in msg or "phường" in msg or "quận" in msg:
                is_strong_intent = True
                logger.info(f"🎯 [OrderHandler] Sticky Intent Activated for session {session_id}")

        logger.info(f"[OrderHandler] Intent: msg='{msg}', strong={is_strong_intent}")

        # 🚀 V4.0: DRAFT-FIRST SLOT FILLER (Deterministic, LLM-Free)
        # When a draft already has items (Turn 1 created it), fill missing slots
        # directly from the current message. This prevents the Dementia Loop where
        # the LLM processes "0949901122" without context and returns items=[].
        lead_data = None
        draft_filled = False
        
        if ctx.order_draft and ctx.order_draft.items:
            missing = ctx.order_draft.missing_slots
            logger.info(f"🧩 [OrderHandler] V4.1 Draft-First Check: Missing Slots={missing}")
            if missing:
                try:
                    # Deterministic Phone Slot Fill
                    if "Số điện thoại" in missing:
                        digits_only = re.sub(r"\D", "", msg)
                        phone_match = re.search(r"0\d{9}", digits_only)
                        if phone_match:
                            validated_phone = validate_vietnam_phone(phone_match.group())
                            if validated_phone:
                                ctx.order_draft.customer_phone = validated_phone
                                draft_filled = True
                                logger.info(f"📞 [OrderHandler] V4.1 Draft-First: Phone slot filled -> {validated_phone}")
                    
                    # Deterministic Address Slot Fill
                    if "Địa chỉ cụ thể" in missing:
                        has_addr_signal = "/" in msg or any(
                            kw in msg for kw in ["đường", "phố", "phường", "quận", "huyện", "xã", "tỉnh", "tp", "số", "ngõ", "ngách", "p.", "q."]
                        )
                        # Elite V4.2: Guard against capturing pure phone numbers as addresses
                        # If the message is mostly digits (e.g. "SĐT: 09xx"), it's likely NOT an address unless signal is strong
                        digits_only = re.sub(r"\D", "", msg)
                        digit_ratio = len(digits_only) / len(msg) if msg else 0
                        is_likely_phone = digit_ratio > 0.3 and not has_addr_signal

                        # If message is long and has digits, it's likely an address (if not a phone)
                        # Elite V5.4: Capture as raw address even if not fully resolved to prevent Dementia Loop
                        if has_addr_signal or (len(msg) > 12 and has_digits and not is_likely_phone):
                            ctx.order_draft.customer_address = ctx.request.message.strip()
                            draft_filled = True
                            logger.info(f"📍 [OrderHandler] 🧩 SLOT FILL (RAW): Address captured -> {ctx.order_draft.customer_address[:30]}...")
                    
                    if draft_filled:
                        # Mark definite intent since customer is actively providing info
                        ctx.order_draft.is_definite_intent = True
                        
                        # V4.0: Resolve address to get shipping_days
                        resolved_shipping_days: str | None = None
                        resolved_addr: str | None = ctx.order_draft.customer_address
                        resolved_possible_provinces: list[str] = []
                        if ctx.order_draft.customer_address:
                            import asyncio as _asyncio
                            geo = await _asyncio.to_thread(location_resolver.resolve, ctx.order_draft.customer_address)
                            if geo.is_valid:
                                resolved_shipping_days = geo.shipping_days
                                resolved_possible_provinces = geo.possible_provinces or []
                                std = ctx.order_draft.customer_address
                                if geo.province and geo.province not in std:
                                    std = f"{std}, {geo.province}"
                                ctx.order_draft.customer_address = std
                                resolved_addr = std
                            elif geo.possible_provinces:
                                resolved_possible_provinces = geo.possible_provinces
                                # V4.2: If ambiguous, mark as NOT definite to trigger provincial ask
                                ctx.order_draft.is_definite_intent = False
                        
                        await xohi_memory.set_order_draft(ctx.session_id, ctx.order_draft.model_dump())
                        logger.info(f"💾 [OrderHandler] V4.1 Draft persisted for SID: {ctx.session_id}")
                        
                        lead_data = ExtractedLead(
                            customer_phone=ctx.order_draft.customer_phone,
                            customer_address=resolved_addr,
                            customer_name=ctx.order_draft.customer_name,
                            items=[LeadOrderItem(**it) for it in ctx.order_draft.items],
                            is_definite_purchase=ctx.order_draft.is_definite_intent,
                            shipping_days=resolved_shipping_days,
                            possible_provinces=resolved_possible_provinces,
                        )
                        ctx.lead_data = lead_data
                        
                        print(f"DEBUG_CONSOLE: ✅ [OrderHandler] 🧩 DRAFT UPDATE: Phone={lead_data.customer_phone}, Address={'SET' if lead_data.customer_address else 'MISSING'}, Items={len(lead_data.items)}")
                        logger.info(f"✅ [OrderHandler] 🧩 DRAFT UPDATE: Phone={lead_data.customer_phone}, Address={'SET' if lead_data.customer_address else 'MISSING'}, Items={len(lead_data.items)}")
                        logger.info(f"✅ [OrderHandler] V4.1 Draft-First Synthesis Complete for SID: {session_id}")
                except Exception as dfe:
                    logger.error(f"❌ [OrderHandler] Draft-First Critical Error: {dfe}")

        # 🚀 2. ATOMIC EXTRACTION (Only if Draft-First didn't handle it)
        if not draft_filled and (is_strong_intent or is_staff_order):
            try:
                lead_data = await lead_extractor.extract_and_convert(
                    ctx.db, ctx.request.message, ctx.session_id, 
                    current_product_slug=ctx.request.product_slug,
                    cart_text=ctx.cart_text
                )
                ctx.lead_data = lead_data

                # 🚀 Elite V3.6: Atomic State Synchronization
                if lead_data:
                    if not ctx.order_draft:
                        ctx.order_draft = OrderDraft(
                            session_id=ctx.session_id,
                            items=[it.model_dump() for it in lead_data.items]
                        )
                    
                    # Update slots
                    if lead_data.customer_phone: ctx.order_draft.customer_phone = lead_data.customer_phone
                    if lead_data.customer_address: ctx.order_draft.customer_address = lead_data.customer_address
                    if lead_data.customer_name: ctx.order_draft.customer_name = lead_data.customer_name
                    if lead_data.items:
                        ctx.order_draft.items = [it.model_dump() for it in lead_data.items]
                    if lead_data.is_definite_purchase:
                        ctx.order_draft.is_definite_intent = True
                    
                    # Persist to Redis
                    await xohi_memory.set_order_draft(ctx.session_id, ctx.order_draft.model_dump())
                    logger.info(f"💾 [OrderHandler] Draft Synchronized for SID: {ctx.session_id}")
            except Exception as e:
                logger.error(f"[OrderHandler] Atomic extraction/draft failed: {e}")

        # 🚀 Elite V5.5: Real-time Draft Monitoring for Sếp
        if ctx.order_draft:
            _items_str = ", ".join([f"{it.get('name', 'SP')} x{it.get('quantity', 1)}" for it in ctx.order_draft.items])
            print(f"DEBUG_CONSOLE: 📦 [OrderDraft] SID: {ctx.session_id} | SPXSL: [{_items_str}] | SĐT: {ctx.order_draft.customer_phone} | ĐỊA CHỈ: {ctx.order_draft.customer_address}")
            logger.info(f"📦 [OrderDraft] SID: {ctx.session_id} Sync: {_items_str} | {ctx.order_draft.customer_phone} | {ctx.order_draft.customer_address}")

        # 🚀 3. DECISION ENGINE (Shadow Checkout & Upsell)
        if lead_data:
            from backend.database import current_tenant_id
            tid = current_tenant_id.get() or "default"

            # Case A: Mập Mờ Số Lượng hoặc Địa Chỉ
            is_definite = lead_data.is_definite_purchase
            has_items = bool(lead_data.items)

            # V4.2: Ambiguity check takes priority over everything except definite success
            if lead_data.possible_provinces and not lead_data.processed_order_id:
                provinces = ", ".join(lead_data.possible_provinces)
                ctx.replies.append(f"{debug_prefix}Dạ địa chỉ của mình trùng tên ở nhiều nơi ({provinces}), Anh/Chị cho Helen xin thêm Tỉnh/Thành phố nhé! 🌸")
                return True

            if not is_definite and not has_items:
                base_price = int(ctx.p_info.price) if ctx.p_info and ctx.p_info.price else 0
                formatted_base = "{:,.0f}".format(base_price).replace(",", ".") + "đ" if base_price > 0 else "đang cập nhật"
                
                header = "Dạ Helen đã ghi nhận thông tin!" if (lead_data.customer_phone or lead_data.customer_address) else "Dạ Helen đã sẵn sàng lên đơn!"
                ctx.replies.append(f"{debug_prefix}{header} 🌸\nAnh/Chị cho em xin **số lượng** sản phẩm muốn lấy để Helen chốt bill cho mình nhé. (Giá đang là: **{formatted_base}**)")
                return True

            # Case B: Thiếu Thông Tin Liên Hệ (Elite V5.4: Hyper-Contextual Responses)
            # Elite V3.1 CTO Guard: Only count address as 'found' if it was successfully resolved (has shipping_days)
            is_address_resolved = bool(lead_data.customer_address and lead_data.shipping_days)
            
            # Logic: If we JUST filled a slot in this turn, we should acknowledge it specifically.
            if not lead_data.customer_phone or not is_address_resolved:
                # 🚀 Elite V3.6: Detect invalid 9-digit phone typos specifically
                raw_phone = re.search(r"0\d{8,10}", msg)
                
                if not lead_data.customer_phone and raw_phone:
                    ctx.replies.append(f"{debug_prefix}Dạ SĐT **{raw_phone.group()}** chị nhắn bị thiếu mất 1 số rồi ạ, chị kiểm tra lại giúp Helen nhé! 🌸")
                elif not lead_data.customer_phone and not is_address_resolved:
                    # CẢ HAI ĐỀU THIẾU
                    ctx.replies.append(f"{debug_prefix}Dạ Helen đã nhận đơn của mình rồi ạ! 🌸 Anh/Chị cho em xin thêm **Số điện thoại và Địa chỉ** cụ thể để em lên bill gửi hàng luôn nhé! ✨")
                elif not lead_data.customer_phone:
                    # CÓ ĐỊA CHỈ NHƯNG THIẾU SĐT
                    ack = "Dạ địa chỉ thì Helen đã thấy rồi."
                    if draft_filled and ctx.order_draft.customer_address in ctx.request.message:
                        ack = f"Dạ Helen đã ghi nhận địa chỉ của mình tại **{lead_data.customer_address}** rồi ạ."
                    ctx.replies.append(f"{debug_prefix}{ack} Anh/Chị cho em xin thêm **Số Điện Thoại** để shipper liên lạc nha! 🌸")
                else:
                    # CÓ SĐT NHƯNG THIẾU ĐỊA CHỈ (HOẶC CHƯA RESOLVED)
                    ack = "Dạ SĐT em lưu 1 bản rồi ạ."
                    if draft_filled and lead_data.customer_phone in msg:
                        ack = f"Dạ Helen đã lưu SĐT **{lead_data.customer_phone}** của mình rồi ạ."
                    
                    # Nếu có địa chỉ thô nhưng chưa resolved (thiếu Tỉnh/TP)
                    if lead_data.customer_address and not is_address_resolved:
                        ctx.replies.append(f"{debug_prefix}{ack} Địa chỉ **{lead_data.customer_address}** mình vừa nhắn Helen chưa rõ là ở Tỉnh/Thành phố nào, Anh/Chị nhắn rõ hơn để em tính phí ship nhé! 🌸")
                    else:
                        ctx.replies.append(f"{debug_prefix}{ack} Anh/Chị cho em xin thêm **Địa chỉ cụ thể** để gửi hàng về tận cửa luôn nhé! 🌸")
                
                # 🚀 Elite V3.6: Interleaved Recovery logic
                if "?" in msg or len(msg) > 60:
                    logger.info("🔀 [OrderHandler] Interleaved Intent detected. Yielding to Consultant.")
                    return False
                
                logger.info(f"✅ [OrderHandler] V5.4 Decision Engine consumed message with response: {ctx.replies[-1][:30]}...")
                return True

            # Case C: Shadow Checkout Thành Công -> Khai hỏa Voucher Intelligence
            if lead_data.processed_order_id:
                # 🚀 Elite V3.6: Cleanup Draft on Success
                await xohi_memory.clear_order_draft(ctx.session_id)
                
                ctx.processed_order_id = lead_data.processed_order_id
                ctx.intent = SupportIntent.PURCHASE

                order_id = str(lead_data.processed_order_id)
                order_obj = (await ctx.db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()

                if order_obj:
                    total_amount = float(order_obj.total_amount or 0)
                    total_qty = sum(int(it.get("quantity", 1)) for it in (order_obj.items or []) if isinstance(it, dict))
                    formatted_price = "{:,.0f}".format(total_amount).replace(",", ".")
                    delivery_info = lead_data.shipping_days or "3-5 ngày"
                    
                    # Tìm Voucher Phù Hợp Tiếp Theo (Upsell Logic)
                    now = datetime.now(timezone.utc)
                    v_stmt = select(Voucher).where(
                        and_(Voucher.deleted_at.is_(None), Voucher.is_active == True, Voucher.tenant_id == tid,
                             or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                             or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
                             Voucher.min_spend > total_amount)  # Tìm voucher cao hơn mức mua hiện tại
                    ).order_by(Voucher.min_spend.asc()).limit(1)
                    
                    next_voucher = (await ctx.db.execute(v_stmt)).scalar_one_or_none()

                    from backend.services.commerce.logic.pricing_engine import PricingEngine
                    
                    # Calculate potential discount to show in the hook
                    from backend.schemas.pricing import PricingInputItem
                    
                    pricing_input = []
                    for it in (order_obj.items or []):
                        if isinstance(it, dict):
                            pricing_input.append(PricingInputItem(
                                product_id=str(it.get("product_id") or ""),
                                name=str(it.get("name", "Sản phẩm")),
                                quantity=int(it.get("quantity", 1)),
                                unit_price=float(it.get("price", 0.0))
                            ))
                    
                    pricing = PricingEngine.calculate(
                        items=pricing_input,
                        available_points=ctx.dna.available_points,
                        points_to_redeem=ctx.dna.available_points,
                        point_value_vnd=ctx.dna.point_value_vnd or 1000.0,
                        base_shipping_fee=0.0 # Assuming subtotal already includes what's needed
                    )

                    # 💎 THE UPSELL & LOYALTY HOOK (Elite V3.1 - Unified)
                    pts_hook = ""
                    if ctx.dna.available_points > 0 and pricing.point_discount_amount > 0:
                        money_pts = "{:,.0f}".format(pricing.point_discount_amount).replace(",", ".")
                        pts_hook = f"⚡ **Ưu đãi thành viên:** Helen thấy mình đang có **{ctx.dna.available_points} điểm**. Mình có muốn Helen dùng luôn để chiết khấu tối đa **{money_pts}đ** cho đơn này không ạ? "

                    if next_voucher and next_voucher.min_spend and (next_voucher.min_spend - total_amount) < 500000:
                        diff = next_voucher.min_spend - total_amount
                        diff_f = "{:,.0f}".format(diff).replace(",", ".")
                        v_val_f = "{:,.0f}".format(next_voucher.value).replace(",", ".") if next_voucher.type != "PERCENT" else f"{next_voucher.value}%"
                        
                        reply = (
                            f"{debug_prefix}Dạ Helen đã gom đơn **{total_qty} mục** ({formatted_price}đ) của mình vào hệ thống. Đơn hàng sẽ về đến tay mình sau khoảng **{delivery_info}** ạ! 🌸\n\n{pts_hook}"
                            f"Đặc biệt, mình chỉ cần mua thêm khoảng **{diff_f}đ** nữa thôi là được áp dụng mã giảm giá **{v_val_f}** rồi đó ạ. Mình có muốn chọn thêm sản phẩm nào để tối ưu voucher luôn không?"
                        )
                    else:
                        reply = (
                            f"{debug_prefix}Dạ Helen chúc mừng Anh/Chị đã đặt hàng thành công! 🌸\nHelen đã chốt gửi đơn đi theo lịch trình:\n"
                            f"- Mã đơn: **{order_id[-8:].upper()}**\n"
                            f"- Sản phẩm: {total_qty} mục\n"
                            f"- Tổng tiền: **{formatted_price}đ** (Lưu giỏ thành công)\n"
                            f"- Dự kiến tới tay: **{delivery_info}**\n\n"
                            f"{pts_hook}\n"
                            f"Anh/Chị nhớ để ý điện thoại để shipper gọi nha! 📞"
                        )
                    
                    ctx.replies.append(reply)
                    return True # Ngắt luồng, trả lời luôn

        return False # Fallthrough (Cho Consultant xử lý tiếp)

