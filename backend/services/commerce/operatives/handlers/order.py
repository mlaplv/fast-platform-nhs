from __future__ import annotations
import logging
import unicodedata
from sqlalchemy import select
from backend.database.models.commerce import Order
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.services.commerce.logic.location_resolver import location_resolver
from backend.schemas.support import SupportIntent

logger = logging.getLogger("api-gateway")

class OrderHandler(BaseHandler):
    """
    ZONE 3: The Order Closer and Status Specialist.
    Priority: Identify purchase intent and extract leads.
    """
    
    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 3: Order Closing. Refined Elite V3.0 Architecture."""
        msg = unicodedata.normalize("NFKC", ctx.request.message.lower().strip())
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
        has_standalone_phone = bool(re.search(r"0\d{9}", msg))
        is_staff_order = any(sp in msg for sp in staff_patterns) and has_digits
        has_buying_intent = any(kw in msg for kw in potential_keywords)
        
        # Elite V3.1 Memory Sync: Trigger if there's buying intent OR a standalone phone number (answering a request)
        is_strong_intent = has_digits and (has_buying_intent or is_staff_order or has_standalone_phone)

        logger.info(f"[OrderHandler] Intent: msg='{msg}', strong={is_strong_intent}")

        # 🚀 2. ATOMIC EXTRACTION 
        lead_data = None
        if is_strong_intent or is_staff_order:
            try:
                lead_data = await lead_extractor.extract_and_convert(
                    ctx.db, ctx.request.message, ctx.session_id, current_product_slug=ctx.request.product_slug
                )
                ctx.lead_data = lead_data
            except Exception as e:
                logger.error(f"[OrderHandler] Atomic extraction failed: {e}")

        # 🚀 3. DECISION ENGINE (Shadow Checkout & Upsell)
        if lead_data:
            from backend.database import current_tenant_id
            tid = current_tenant_id.get() or "default"

            # Case A: Mập Mờ Số Lượng (Đã Bị Chặn Bằng Lệnh Không Có Items ở LeadExtractor)
            is_definite = lead_data.is_definite_purchase
            has_items = bool(lead_data.items)

            if not is_definite and not has_items:
                if lead_data.possible_provinces:
                    provinces = ", ".join(lead_data.possible_provinces)
                    ctx.replies.append(f"{debug_prefix}Dạ địa chỉ của mình trùng tên ở nhiều nơi ({provinces}), Anh/Chị cho Helen xin thêm Tỉnh/Thành phố nhé! 🌸")
                    return True

                base_price = int(ctx.p_info.price) if ctx.p_info and ctx.p_info.price else 0
                formatted_base = "{:,.0f}".format(base_price).replace(",", ".") + "đ" if base_price > 0 else "đang cập nhật"
                
                header = "Dạ Helen đã ghi nhận thông tin!" if (lead_data.customer_phone or lead_data.customer_address) else "Dạ Helen đã sẵn sàng lên đơn!"
                ctx.replies.append(f"{debug_prefix}{header} 🌸\nAnh/Chị cho em xin **số lượng** sản phẩm muốn lấy để Helen chốt bill cho mình nhé. (Giá đang là: **{formatted_base}**)")
                return True

            # Case B: Thiếu Thông Tin Liên Hệ
            # Elite V3.1 CTO Guard: Only count address as 'found' if it was successfully resolved (has shipping_days)
            is_address_resolved = bool(lead_data.customer_address and lead_data.shipping_days)
            
            if not lead_data.customer_phone or not is_address_resolved:
                if not lead_data.customer_phone and not is_address_resolved:
                    ctx.replies.append(f"{debug_prefix}Dạ Helen đã nhận đơn của mình rồi ạ! 🌸 Anh/Chị cho em xin thêm **Số điện thoại và Địa chỉ** cụ thể để em lên bill gửi hàng luôn nhé! ✨")
                elif not lead_data.customer_phone:
                    ctx.replies.append(f"{debug_prefix}Dạ địa chỉ thì Helen đã thấy rồi. Anh/Chị cho em xin thêm **Số Điện Thoại** để shipper liên lạc nha! 🌸")
                else:
                    ctx.replies.append(f"{debug_prefix}Dạ SĐT em lưu 1 bản rồi ạ. Anh/Chị cho em xin thêm **Địa chỉ cụ thể** để gửi hàng về tận cửa luôn nhé! 🌸")
                return True

            # Case C: Shadow Checkout Thành Công -> Khai hỏa Voucher Intelligence
            if lead_data.processed_order_id:
                ctx.processed_order_id = lead_data.processed_order_id
                ctx.intent = SupportIntent.PURCHASE

                order_id = str(lead_data.processed_order_id)
                order_obj = (await ctx.db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()

                if order_obj:
                    total_amount = float(order_obj.total_amount or 0)
                    total_qty = sum(int(it.get("quantity", 1)) for it in (order_obj.items or []) if isinstance(it, dict))
                    
                    # Tìm Voucher Phù Hợp Tiếp Theo (Upsell Logic)
                    now = datetime.now(timezone.utc)
                    v_stmt = select(Voucher).where(
                        and_(Voucher.deleted_at.is_(None), Voucher.is_active == True, Voucher.tenant_id == tid,
                             or_(Voucher.start_date.is_(None), Voucher.start_date <= now),
                             or_(Voucher.end_date.is_(None), Voucher.end_date >= now),
                             Voucher.min_spend > total_amount)  # Tìm voucher cao hơn mức mua hiện tại
                    ).order_by(Voucher.min_spend.asc()).limit(1)
                    
                    next_voucher = (await ctx.db.execute(v_stmt)).scalar_one_or_none()

                    formatted_price = "{:,.0f}".format(total_amount).replace(",", ".")
                    delivery_info = location_resolver.resolve(order_obj.customer_address or "").shipping_days or "2-3 ngày"

                    # 💎 THE UPSELL & LOYALTY HOOK (Elite V3.0)
                    pts_hook = ""
                    if ctx.dna.available_points > 0:
                        money_pts = "{:,.0f}".format(ctx.dna.available_points * ctx.dna.point_value_vnd).replace(",", ".")
                        pts_hook = f"⚡ **Ưu đãi thành viên:** Mình đang có **{ctx.dna.available_points} điểm** tích lũy (~{money_pts}đ). Mình có muốn Helen dùng luôn để chiết khấu trực tiếp cho đơn này không ạ? "

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

