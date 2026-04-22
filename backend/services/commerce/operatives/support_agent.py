"""
Support Agent Operative — SUPPORT_NAME_CLIENT (Architect's Edition)
==================================================================
Elite V2.2: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations

import asyncio
import json
import os
import logging
import re
import time
import uuid
from typing import Optional, cast, Union, Dict, Type, List, Tuple
from pydantic import BaseModel, Field, ConfigDict, JsonValue
from pydantic_ai import Agent, RunContext
from sqlalchemy import select, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase, ProductVariant, Order
from backend.database.models.content import Category
from backend.database.models.system import SupportChatHistory
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse, SupportProductInfo
from backend.schemas.order import OrderDraft
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
from backend.database.alchemy_config import alchemy_config
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory
from backend.utils.security import GeminiSecurity

from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext
from backend.services.commerce.operatives.router import SupportRouter

logger = logging.getLogger("api-gateway")

class AgenticSupportResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str = Field(..., description="Văn bản phản hồi tự nhiên. Nếu khách muốn xem hình hoặc hỏi sản phẩm, hãy dùng PRODUCT_CARD.")
    intent: str = Field(..., description="MỘT trong các chuỗi sau: 'ORDER_STATUS', 'ESCALATE', 'POLICY_QUERY', 'PRICE_QUERY', 'PURCHASE', 'GENERAL_ADVICE', 'UNKNOWN'")
    ui_component: Optional[str] = Field(default=None, description="PRODUCT_CARD | POLICY_CARD | NONE")

class FastIntentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    intent: str = Field(..., description="GREETING, POLICY, PRODUCT, ORDER, PURCHASE, OTHER")
    confidence: float = Field(default=1.0)
    quick_reply: Optional[str] = None

class SupportAgentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENTS — Singleton (Elite V2.2 Standards)
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1, 
)

class FastIntentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    customer_name: str = "Quý khách"

_fast_intent_agent: Agent[FastIntentDeps, FastIntentResponse] = Agent(
    output_type=FastIntentResponse,
    system_prompt=(
        "You are Helen - a high-end Cosmetics Specialist. Classify user message into: "
        "GREETING, POLICY, PRODUCT, ORDER, PURCHASE, OTHER. "
        "IMPORTANT: If it's a simple greeting, provide a friendly quick_reply in Vietnamese. "
        "Always personalize the quick_reply using the specific customer's name from deps if provided. "
        "DO NOT use the word 'Sếp' or 'bạn'. Use 'Quý khách' or 'Anh/Chị' if the name is generic. "
        "Tone: Elegant, professional, welcoming, using icons like 🌸, ✨. "
        "Confidence must be 0.0 to 1.0."
    )
)

@_support_ai_agent.tool
async def search_knowledge_base(ctx: RunContext[SupportAgentDeps], query: str) -> str:
    """LAYER 3: Tìm kiếm mờ trong toàn bộ kho tri thức."""
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    repo = SupportKnowledgeRepository(session=ctx.deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.search_relevant_knowledge(ctx.deps.db, query)

async def _fetch_product_context(db: AsyncSession, slug: Optional[str]) -> Tuple[str, Optional[SupportProductInfo]]:
    """Fetch product info via SQLAlchemy 2.0 Scalar projection."""
    if not slug: return "", None
    # Elite V2.2: Skip context fetch for static/policy pages to reduce log noise
    if any(p in slug for p in ["chinh-sach", "gioi-thieu", "tuyen-dung", "dieu-khoan", "thanh-toan", "kiem-hang", "bao-hanh"]):
        return "", None
        
    try:
        stmt = (
            select(
                ProductBase.id,
                ProductBase.name,
                ProductBase.price,
                ProductBase.discount_price,
                ProductBase.slug,
                ProductBase.stock,
                ProductBase.short_description,
                ProductBase.images
            )
            .where(and_(ProductBase.slug == slug, ProductBase.deleted_at.is_(None), ProductBase.status == "ACTIVE"))
        )
        res = await db.execute(stmt)
        p_row = res.first()
        if not p_row: return "", None
        img_url = p_row.images[0] if p_row.images and len(p_row.images) > 0 else None
        p_info = SupportProductInfo(
            id=str(p_row.id), 
            name=p_row.name, 
            price=float(p_row.price or 0), 
            price_display=f"{int(p_row.discount_price or p_row.price or 0):,}đ".replace(",", "."), 
            slug=p_row.slug or "",
            image_url=img_url,
            stock=p_row.stock
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {p_row.name}\nMô tả: {p_row.short_description}\nGiá niêm yết: {p_row.price} VND\n"
        if p_row.discount_price: ctx += f"Giá khuyến mãi: {p_row.discount_price} VND\n"
        ctx += f"Tồn kho thực tế: {p_row.stock or 0} sản phẩm\n"
        return ctx, p_info
    except Exception as e:
        logger.warning("[SupportAgent] Context sweep failure: %s", e)
        return "", None

def _sanitize_response(text: str) -> str:
    """Surgical leak prevention (Elite V2.2)."""
    # 1. Hide AI thought tags
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    # 2. Redact internal paths
    clean = re.sub(r"/\w+/\w+/\w+", "[REDACTED_PATH]", clean)
    # 3. Privacy Guard: Mask Phone Numbers (Vietnamese format)
    clean = re.sub(r"(0|84|(\+84))(\d{2,3})[\s\.\-]?(\d{3})[\s\.\-]?(\d{3,4})", r"\1\3****\5", clean)
    return clean.strip()

class SupportAgentOperative(BaseAgentOperative):
    """Refined Architect-level Operative."""
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent"):
        super().__init__(agent_id=agent_id)
        self.router = SupportRouter()
        self._arq_pool = None

    async def _get_arq_pool(self) -> object:
        """Resource handle for arq Pool. Elite V2.2: Using 'object' instead of 'Any' for strict typing."""
        if self._arq_pool is None:
            from arq import create_pool
            from backend.infra.arq_config import get_redis_settings
            self._arq_pool = await create_pool(get_redis_settings())
        return self._arq_pool

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return SupportRequest

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        """Encrypted transactional history persistence."""
        try:
            # Shield internal trigger from history
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                enc_user_msg = GeminiSecurity.encrypt(user_msg)
                msg_user = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
                db.add(msg_user)

            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            msg_ai = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add(msg_ai)
            await db.flush()
            logger.info("[SupportAgent] Persisted chat segment for SID: %s", session_id)
            
            # 🚀 Elite V2.2: Proactive Follow-up (Feedback Loop)
            # Schedule a reminder in 1 hour if the user doesn't respond.
            # Only if this is a real user message (not a system trigger)
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                try:
                    redis = await self._get_arq_pool()
                    await redis.enqueue_job(
                        "helen_follow_up_job",
                        session_id=session_id,
                        _defer_by=3600, # 1 hour (3600s)
                        _job_id=f"followup:{session_id}:{int(time.time())}", 
                        _queue_name="high"
                    )
                except Exception as arqe:
                    logger.warning("[SupportAgent] Follow-up scheduling failed: %s", arqe)
        except Exception as exc:
            logger.warning("[SupportAgent] Saving failed: %s. Rolling back to clear session state.", exc)
            await db.rollback()

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        """Context-window hydration (Elite V2.2). Enhanced to 10 turns with character clipping."""
        try:
            stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)).limit(10)
            history_rows = (await db.execute(stmt)).scalars().all()
            if not history_rows: return ""
            h_parts = []
            total_chars = 0
            MAX_TOTAL_CHARS = 5000 # Safety cap for context window

            for r in reversed(history_rows):
                h_content = GeminiSecurity.decrypt(r.content or "")
                if h_content == HELEN_FOLLOW_UP_TRIGGER:
                    continue # Elite V2.2: Shield internal triggers
                
                # Làm sạch dữ liệu log chat (trunc history) để tránh bùng nổ context
                # Giới hạn mỗi tin nhắn 300 ký tự
                if len(h_content) > 300:
                    h_content = h_content[:300] + "... [TRUNCATED_HISTORY]"
                
                # Global Context Guard
                if total_chars + len(h_content) > MAX_TOTAL_CHARS:
                    break

                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
                total_chars += len(h_content)

            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n" if h_parts else ""
        except: return ""

    async def _fetch_neural_dna(
        self, 
        db: AsyncSession, 
        session_id: str, 
        lead_phone: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> NeuralDNA:
        """Hydrate Neural DNA from Loyalty & Order History (Elite V3.0: Military-Grade)."""
        try:
            mem = await xohi_memory.get_user_context(session_id)
            if mem and "dna" in mem:
                # Still check for phone/id updates if user just provided them
                dna_obj = NeuralDNA.model_validate(mem["dna"])
                if not lead_phone and not user_id:
                    return dna_obj
            
            from backend.database.models.commerce import Order, UserLoyalty
            from backend.database.models.system import SystemSetting
            from backend.services.commerce.loyalty import LoyaltyService
            
            # --- 1. Identity Resolution ---
            final_user_id = user_id
            customer_name = None
            
            if not final_user_id and lead_phone:
                from backend.database.models.auth import User
                u_stmt = select(User.id, User.name).where(User.phone == lead_phone).limit(1)
                u_row = (await db.execute(u_stmt)).first()
                if u_row:
                    final_user_id = u_row[0]
                    customer_name = u_row[1]
            elif final_user_id:
                from backend.database.models.auth import User
                u_stmt = select(User.name).where(User.id == final_user_id).limit(1)
                customer_name = await db.scalar(u_stmt)

            available_pts = 0
            pt_value = 1000
            
            # --- 2. Loyalty & Integrity (Military Grade) ---
            if final_user_id:
                # R00: Verify integrity seal before trusting point balance
                if await LoyaltyService.verify_loyalty_integrity(db, final_user_id):
                    l_stmt = select(UserLoyalty).where(UserLoyalty.user_id == final_user_id)
                    loyalty = (await db.execute(l_stmt)).scalar_one_or_none()
                    if loyalty:
                        available_pts = loyalty.available_points
                else:
                    logger.critical("[SECURITY] Loyalty Tampering detected for user: %s", final_user_id)

            # --- 3. Point Value Config ---
            s_stmt = select(SystemSetting).where(SystemSetting.key == "LOYALTY_POINT_VALUE_VND")
            setting = (await db.execute(s_stmt)).scalar_one_or_none()
            if setting and isinstance(setting.value, dict) and "value" in setting.value:
                pt_value = int(setting.value["value"])

            # --- 4. Order History for Segmentation ---
            total_spent = 0.0
            order_count = 0
            if lead_phone or final_user_id:
                cond = []
                if lead_phone: cond.append(Order.customer_phone == lead_phone)
                if final_user_id: cond.append(Order.user_id == final_user_id)
                
                stmt = select(Order).where(and_(or_(*cond), Order.status == "DELIVERED"))
                orders = (await db.execute(stmt)).scalars().all()
                order_count = len(orders)
                total_spent = sum(float(o.total_amount or 0) for o in orders)

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
            return dna
        except Exception as e:
            logger.warning("[SupportAgent] DNA fetch failed: %s", e)
            import traceback
            logger.error(traceback.format_exc())
            return NeuralDNA()

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """Architecture V2.5: Orchestrated Specialist Pipeline."""
        session_id = request.session_id or str(uuid.uuid4())
        
        # 🚀 1. HYDRATE CONTEXT (Zero-Leak Hydration)
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang đồng bộ DNA Helen..."})
        
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug)
        hist_text = await self._fetch_chat_context(db, session_id)
        dna = await self._fetch_neural_dna(
            db, 
            session_id, 
            lead_phone=request.customer_phone,
            user_id=request.user_id
        )
        
        logger.info(f"🧠 [SupportAgent] Processing Brain Logic for Session: {session_id}")
        logger.info(f"🛒 [SupportAgent] Cart Items Count: {len(request.cart_items) if request.cart_items else 0}")
        logger.info(f"💰 [SupportAgent] Pricing Context Present: {bool(request.pricing_context)}")
        logger.debug(f"📜 [SupportAgent] History Window: {hist_text[:100]}...")
        
        # 🚀 1.0.1: Layer 1 Memory (Knowledge Map) - Elite V2.2 Protocol
        try:
            from backend.database.repositories import SupportKnowledgeRepository
            from backend.services.commerce.support_knowledge import SupportKnowledgeService
            repo = SupportKnowledgeRepository(session=db)
            kb_service = SupportKnowledgeService(repo=repo)
            kb_index = await kb_service.get_knowledge_index(db)
        except Exception as kbe:
            kb_index = ""

        # 🚀 1.1: Fetch Integration Config (Elite V2.2)
        zalo_on = await xohi_memory.client.get("system:zalo_enabled") != "0"
        messenger_on = await xohi_memory.client.get("system:messenger_enabled") != "0"

        # 🚀 1.2: Elite FOMO Sync
        from backend.services.commerce.logic.fomo_service import fomo_service
        active_visitors = await fomo_service.get_active_visitors_count()

        # 🚀 1.3: Elite V3.6: Order Draft Hydration
        raw_draft = await xohi_memory.get_order_draft(session_id)
        order_draft = OrderDraft.model_validate(raw_draft) if raw_draft else None

        # 🚀 Elite V5.3: ULTRA-LEAN GROUND TRUTH PROTOCOL
        from backend.services.commerce.promotion import PromotionService
        from backend.database.models.commerce import ProductBase, ProductVariant
        from sqlalchemy import select
        
        # 1. REPORT GENERATION (What the customer sees)
        cart_lines = []
        if request.cart_items:
            for item in request.cart_items:
                p_raw = item.get("product", {})
                v_raw = item.get("variant", {})
                qty = item.get("quantity", 1)
                p_id = p_raw.get("id")
                if not p_id: continue
                
                p_db = (await db.execute(select(ProductBase).where(ProductBase.id == p_id))).scalar_one_or_none()
                v_id = v_raw.get("id")
                v_db = None
                if v_id:
                    v_db = (await db.execute(select(ProductVariant).where(ProductVariant.id == v_id))).scalar_one_or_none()

                # Use Base Price for parity with Checkout UI "TỔNG" line
                p_price = float(v_db.price if v_db else (p_db.price if p_db else (p_raw.get("price") or 0)))
                p_name = p_db.name if p_db else p_raw.get("name", "Sản phẩm")
                # Elite V5.5: Safe variant label resolution (ProductVariant model has no 'name' field)
                v_label = v_raw.get("name") or v_raw.get("label")
                if v_label:
                    p_name += f" ({v_label})"
                
                cart_lines.append(f"- {p_name}: {qty} x {int(p_price):,}đ = {int(p_price * qty):,}đ".replace(",", "."))

        # 🚀 Elite V5.7: Optimized Pricing Breakdown (Ground Truth vs Fallback)
        pb = await self._prepare_pricing_breakdown(db, request, dna)
        
        cart_text = "\n[CHI TIẾT GIỎ HÀNG THỰC TẾ]\n" + "\n".join(cart_lines) + "\n" if cart_lines else "\n[GIỎ HÀNG THỰC]: Trống.\n"
        if pb.get("subtotal", 0) > 0:
            cart_text += f"\n[BẢNG TÍNH TOÁN CHI TIẾT - ELITE GROUND TRUTH]\n"
            if pb.get("is_fallback"):
                cart_text += "⚠️ [LƯU Ý HỆ THỐNG]: Đang dùng logic tính toán dự phòng. Hãy nhắc khách kiểm tra lại giỏ hàng và Voucher đã áp dụng trên trang Checkout để có con số chính xác tuyệt đối.\n"
            cart_text += f"1. Tổng tạm tính (Sản phẩm): {int(pb['subtotal']):,}đ\n".replace(",", ".")
            if pb.get("combo_discount", 0) > 0: cart_text += f"2. Chiết khấu Combo: -{int(pb['combo_discount']):,}đ\n".replace(",", ".")
            
            # Elite V5.8: Display REAL voucher names (SPLIT: Product vs Shipping)
            applied_v = pb.get("applied_vouchers") or []
            prod_v_names = ", ".join([v.get("name", v.get("id", "Voucher")) for v in applied_v if v.get("type") != "SHIPPING"])
            ship_v_names = ", ".join([v.get("name", v.get("id", "Voucher")) for v in applied_v if v.get("type") == "SHIPPING"])

            if pb.get("voucher_discount", 0) > 0: 
                v_label = f"({prod_v_names})" if prod_v_names else ""
                cart_text += f"3. Giảm giá Voucher {v_label}: -{int(pb['voucher_discount']):,}đ\n".replace(",", ".")
            
            cart_text += f"4. Phí vận chuyển: {int(pb.get('base_shipping_fee', 0)):,}đ\n".replace(",", ".")
            if pb.get("shipping_discount", 0) > 0: 
                v_label = f"(mã {ship_v_names})" if ship_v_names else ""
                cart_text += f"   - Giảm phí ship {v_label}: -{int(pb['shipping_discount']):,}đ\n".replace(",", ".")
            
            if pb.get("point_discount_amount", 0) > 0:
                cart_text += f"5. Điểm tích lũy (Khách dùng {pb['points_redeemed']} pts):\n"
                cart_text += f"   - Giảm giá: -{int(pb['point_discount_amount']):,}đ\n".replace(",", ".")
                cart_text += f"   - [HỆ THỐNG ĐÃ TÍNH SẴN]: Khách chỉ được giảm tối đa 1% giá trị đơn để bảo vệ quyền lợi Sếp.\n"
            
            cart_text += f"\n👉 TỔNG THANH TOÁN CUỐI CÙNG: {int(pb['final_payable']):,}đ\n".replace(",", ".")
            cart_text += f"👉 DỰ KIẾN TÍCH LŨY: +{pb['points_to_earn']} điểm.\n"
            cart_text += f"--------------------------------\n"
            
            # 🚀 Elite V4.9: INTELLIGENT BEST-DEAL RESOLUTION (FOMO)
            from backend.database.models.promotion import Voucher
            all_vouchers = (await db.execute(select(Voucher).where(Voucher.is_active == True))).scalars().all()
            
            best_v = None
            max_sav = 0
            
            for v in all_vouchers:
                if pb["subtotal"] < (v.min_spend or 0): continue
                
                sav = 0
                if v.type == "FIXED": sav = v.value
                elif v.type == "PERCENT":
                    sav = (pb["subtotal"] * v.value) / 100
                    if v.max_discount: sav = min(sav, v.max_discount)
                elif v.type == "SHIPPING": sav = 30000.0 # Standard ship fee value
                
                if sav > max_sav:
                    max_sav = sav
                    best_v = v

            if best_v:
                cart_text += f"\n[CHỈ THỊ FOMO CHO HELEN]:\n"
                cart_text += f"- Mã ưu đãi TỐT NHẤT hiện tại: '{best_v.id}' (Giảm ~{int(max_sav):,}đ)\n".replace(",", ".")
                if pb["voucher_discount"] < (max_sav - 1000): # Allow for small floating point diff
                    cart_text += f"- [CẢNH BÁO]: Khách chưa dùng mã tốt nhất. HÃY THUYẾT PHỤC KHÁCH DÙNG MÃ '{best_v.id}' ĐỂ TIẾT KIỆM TỐI ĐA!\n"
                else:
                    cart_text += f"- [XÁC NHẬN]: Khách đã dùng mã tối ưu. Hãy khen khách thông thái và chốt đơn ngay.\n"
            
            # Upsell to next tier if close
            next_v = next((v for v in all_vouchers if (v.min_spend or 0) > pb["subtotal"]), None)
            if next_v:
                gap = next_v.min_spend - pb["subtotal"]
                if gap < 300000:
                    cart_text += f"- Gợi ý mua thêm: Chỉ thiếu {int(gap):,}đ nữa là dùng được mã '{next_v.id}' (Giảm cực sâu).\n".replace(",", ".")

            cart_text += f"--------------------------------\n"


        ctx = SupportContext(
            db=db,
            request=request,
            session_id=session_id,
            dna=dna,
            product_ctx=ctx_text,
            history_text=hist_text,
            knowledge_index=kb_index,
            p_info=p_info,
            zalo_enabled=zalo_on,
            messenger_enabled=messenger_on,
            active_visitors=active_visitors,
            product_stock=p_info.stock if p_info else 0,
            order_draft=order_draft,
            cart_text=cart_text
        )
        
        # 🚀 2. EXECUTE PIPELINE (The Specialists)
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": f"Đang điều phối chuyên gia {dna.segment}..."})
        
        try:
            ctx = await self.router.process(ctx)
        except Exception as pe:
            logger.error(f"[SupportAgent] Router Pipeline Failed: {pe}")
            await db.rollback()
            # Allow to proceed to fallback reply
        
        # 🚀 3. POST-PROCESSING (Verification & Finalization)
        # We join all collected replies into one natural message
        final_reply = " ".join(ctx.replies).strip() if ctx.replies else "[fallback] Dạ Helen xin lỗi, hiện tại em đang bận xử lý dữ liệu một chút. Anh/Chị vui lòng nhập câu hỏi rõ hơn hoặc chờ em giây lát nhé! 🌸"
        
        # 🚀 Elite V3.6: Stateful Response Synthesis (The Closing Hook)
        # Elite V5.4: Inhibit redundant hooks if specialized handler already replied or intent is clear
        if ctx.order_draft and not ctx.order_draft.is_complete and ctx.intent != SupportIntent.PURCHASE:
            # Skip hook if specialists (like OrderHandler) already provided a slot-filling reply
            if not ctx.replies or len(ctx.replies) == 0:
                missing = ctx.order_draft.missing_slots
                if missing:
                    hook = f"\n\n(Dạ em vẫn đang chờ {', '.join(missing)} của mình để hoàn tất đơn hàng đó ạ! 🌸)"
                    if hook not in final_reply:
                        final_reply += hook

        # 🚀 V4.2: Universal UI Metadata - Always include draft state for UI/Debugging
        if ctx.order_draft:
            if not ctx.ui_metadata:
                ctx.ui_metadata = {}
            ctx.ui_metadata.update({
                "order_draft": ctx.order_draft.model_dump(mode='json'),
                "missing_slots": ctx.order_draft.missing_slots,
                "is_definite": ctx.lead_data.is_definite_purchase if ctx.lead_data else False
            })
        
        safe_reply = _sanitize_response(final_reply) or "[fallback] Dạ em đang kết nối lại, Anh/Chị thông cảm nhé!"
        
        # Final Intent and Component Logic
        final_intent = ctx.intent or SupportIntent.UNKNOWN
        
        # Hydrate ui_metadata if component is PRODUCT_CARD
        if ctx.ui_component == "PRODUCT_CARD" and p_info:
            if not ctx.ui_metadata: ctx.ui_metadata = {}
            ctx.ui_metadata.update({"type": "PRODUCT_CARD", "data": p_info.model_dump()})

        # 🚀 4. PERSISTENCE (Atomic Commit)
        await self._save_history(
            db, session_id, request.message, safe_reply, final_intent, 
            request.product_slug, dna.customer_name or request.customer_name, 
            ctx.lead_data.customer_phone if ctx.lead_data else None
        )
        # 🚀 Elite V2.2: Presence Tracking (Heartbeat)
        # Mark user as online for 2 minutes (120s)
        try:
            await xohi_memory.client.set(f"support:presence:{session_id}", "1", ex=120)
        except Exception as pe:
            logger.warning("[SupportAgent] Presence update failed: %s", pe)

        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        
        # 🚀 Elite V2.2: Ensure data is flushed for other agents to see
        await db.flush()
        
        return SupportResponse(
            ok=True, 
            reply=safe_reply, 
            intent=final_intent, 
            session_id=session_id, 
            product_info=p_info, 
            status="DONE", 
            ui_metadata=ctx.ui_metadata,
            processed_order_id=ctx.processed_order_id
        )

    async def _prepare_pricing_breakdown(self, db: AsyncSession, request: SupportRequest, dna: NeuralDNA) -> Dict[str, Union[float, int, bool]]:
        """
        [ELITE V5.7] Centralized Pricing Intelligence.
        Consumes Frontend Ground Truth OR falls back to specialized PricingEngine with Bundle support.
        """
        # 1. GROUND TRUTH HIT
        if request.pricing_context and request.pricing_context.subtotal > 0:
            ctx_gt = request.pricing_context
            return {
                "subtotal": ctx_gt.subtotal,
                "combo_discount": ctx_gt.combo_discount,
                "voucher_discount": ctx_gt.voucher_discount,
                "final_shipping_fee": ctx_gt.shipping_fee,
                "base_shipping_fee": 30000.0 if (ctx_gt.shipping_fee > 0 or ctx_gt.subtotal < 2000000) else 0.0,
                "shipping_discount": 30000.0 if (ctx_gt.shipping_fee == 0 and ctx_gt.subtotal < 2000000) else 0.0,
                "point_discount_amount": ctx_gt.point_discount,
                "shipping_discount": ctx_gt.shipping_discount,
                "final_payable": ctx_gt.final_total,
                "points_redeemed": ctx_gt.points_redeemed,
                "points_to_earn": int(ctx_gt.final_total // 100000),
                "applied_vouchers": ctx_gt.applied_vouchers,
                "is_fallback": False
            }

        # 2. FALLBACK (Heuristic calculations)
        from backend.services.commerce.logic.pricing_engine import PricingEngine
        from backend.schemas.pricing import PricingInputItem
        from backend.services.commerce.promotion import PromotionService
        
        fallback_items = []
        for it in (request.cart_items or []):
            p_raw = it.get("product", {})
            p_id = p_raw.get("id")
            if not p_id: continue
            # Elite V5.6: Use ORIGINAL PRICE in fallback to match Checkout UI
            p_pr = float(p_raw.get("price") or p_raw.get("discountPrice") or 0)
            fallback_items.append(PricingInputItem(product_id=str(p_id), name=p_raw.get("name", "SP"), quantity=it.get("quantity", 1), unit_price=p_pr))
        
        if not fallback_items:
            return {"subtotal": 0, "final_payable": 0, "points_to_earn": 0, "is_fallback": True}

        pricing = PricingEngine.calculate(
            items=fallback_items,
            vouchers=[], 
            combo_deals=await PromotionService.get_active_combo_deals(db),
            points_to_redeem=0, 
            available_points=dna.available_points,
            point_value_vnd=dna.point_value_vnd or 1000.0,
            base_shipping_fee=30000.0 if sum(i.unit_price * i.quantity for i in fallback_items) < 2000000 else 0.0
        )
        return {
            "subtotal": pricing.subtotal,
            "combo_discount": pricing.combo_discount,
            "voucher_discount": pricing.voucher_discount,
            "base_shipping_fee": pricing.base_shipping_fee,
            "shipping_discount": pricing.shipping_discount,
            "final_shipping_fee": pricing.final_shipping_fee,
            "point_discount_amount": pricing.point_discount_amount,
            "final_payable": pricing.final_payable,
            "points_to_earn": pricing.points_to_earn,
            "points_redeemed": pricing.points_redeemed,
            "is_fallback": True
        }

    async def chat(self, request: Union[SupportRequest, dict], **kwargs: object) -> SupportResponse:
        """
        Elite V2.5: Entry Protocol.
        Supports both direct API (SupportRequest) and Worker calls (dict).
        """
        # 0. Normalize Request & DB Session
        if isinstance(request, dict):
            request = SupportRequest.model_validate(request)
            
        db = cast(Optional[AsyncSession], kwargs.get("db"))
        if not db:
            # Lifecycle: Worker Context — Create standalone session
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as standalone_db:
                res = await self._chat_internal(request, standalone_db)
                await standalone_db.commit()
                logger.info("[SupportAgent] Worker commit successful for SID: %s", request.session_id)
                return res
        
        return await self._chat_internal(request, db)

    async def _chat_internal(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """Internal dispatch logic with Elite V2.2 Inhibition Guards."""
        session_id = request.session_id or str(uuid.uuid4())

        # 🚀 Elite V3.0: Early DNA Hydration for Personalized Fast-Path & Contextual Awareness
        dna = await self._fetch_neural_dna(
            db, 
            session_id, 
            lead_phone=request.customer_phone,
            user_id=request.user_id
        )
        # 🚀 Elite v3.2 Identity Hardening
        c_name = dna.customer_name or request.customer_name or "Quý khách"
        if c_name in ["Khách ẩn danh", "Sếp"]: c_name = "Quý khách"

        # 🚀 Elite V2.2: Inhibition Guards (Handover & Global Control)
        # 1. Global Switch
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0":
            return SupportResponse(
                ok=False, 
                reply="Hệ thống tư vấn AI hiện đang bảo trì. Vui lòng để lại lời nhắn cho dược sĩ ạ.", 
                intent=SupportIntent.UNKNOWN, 
                session_id=session_id, 
                status="FAILED"
            )

        # 2. Staff Takeover (Inverse Logic: 0 = Human Active / AI Blocked)
        takeover_val = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if takeover_val == "0":
            logger.info("[SupportAgent] Helen inhibited for SID: %s (Human Takeover)", session_id)
            return SupportResponse(
                ok=True, 
                reply="Dược sĩ đang trực tiếp hỗ trợ mình ạ. Vui lòng đợi trong giây lát nhé! ✨", 
                intent=SupportIntent.UNKNOWN, 
                session_id=session_id, 
                status="DONE"
            )
        
        # 🚀 FAST-PATH (Intent Classification Only)
        logger.info("[SupportAgent] Entering Fast-Path classification for SID: %s", session_id)
        try:
            # Elite V2.2: Shield sensitive terms before fast-path classification
            masked_msg = await self._mask_sensitive_medical_terms(request.message)
            fast_res = await trinity_bridge.run(
                _fast_intent_agent, 
                masked_msg, 
                deps=FastIntentDeps(customer_name=c_name),
                role=trinity_bridge.ROLE_FAST, 
                timeout=2.0,
                safety_none=True
            )
            f_data = cast(FastIntentResponse, fast_res)
            
            if f_data.intent == "GREETING" and f_data.quick_reply and not request.cart_items:
                await self._save_history(
                    db, session_id, request.message, f_data.quick_reply, 
                    SupportIntent.GENERAL_ADVICE, request.product_slug,
                    c_name, request.customer_phone
                )
                await db.flush()
                return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
        except Exception as e:
            logger.warning("[SupportAgent] Fast-Path Bypass: %s", e)

        # 🚀 L0.5: SYNCHRONOUS HEURISTIC FAST-PATH (Elite V2.5 — Race Condition Fix)
        _, p_info = await _fetch_product_context(db, request.product_slug)
        heuristic_res = await self._try_heuristic_sync(request, db, session_id, p_info, c_name)
        if heuristic_res:
            return heuristic_res

        # 🚀 DEEP BRAIN (Background Task) — for complex queries only
        logger.info("[SupportAgent] Falling back to Deep-Brain for SID: %s", session_id)
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        logger.info("[SupportAgent] Deep-Brain task enqueued: %s for SID: %s", task_id, session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

    async def _try_heuristic_sync(self, request: SupportRequest, db: AsyncSession, session_id: str, p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None) -> Optional[SupportResponse]:
        """
        Elite V3.0: Synchronous Heuristic Fast-Path.
        - INFO_ADDRESS / INFO_HOTLINE → đọc SystemSettings (Redis cache) — không cần LLM, < 100ms.
        - PRICE_QUERY → đọc p_info trực tiếp — không cần LLM, < 100ms.
        - INFO_INGREDIENTS / INFO_SHIPPING → fall-through đến Deep-Brain (context-dependent).
        - Xóa sự phụ thuộc sai vào bảng support_knowledge cho dữ liệu cấu trúc.
        """
        import os
        import json as _json
        
        msg_norm = request.message.lower().strip()
        debug_prefix = "" if os.getenv("HELEN_DEBUG", "0") != "1" else "[L0.5] "
        
        # 1. INFO_INGREDIENTS & INFO_SHIPPING → Fall-through (Trả về None ngay lập tức để Deep Brain chạy Tool)
        kws_ing = ["thành phần", "chiết xuất", "gồm những gì", "làm từ gì", "thảo dược gì", "công thức", "thành phần thuốc", "chất gì", "có gì trong thuốc"]
        kws_ship = ["ship", "phí", "giao hàng", "vận chuyển", "nhận hàng"]
        if any(kw in msg_norm for kw in kws_ing) or any(kw in msg_norm for kw in kws_ship):
            logger.info("⚡ [SupportAgent] Sync Heuristic: Fall-through to Deep Brain for INGREDIENTS/SHIPPING")
            return None

        # 2. PRICE_QUERY → Xử lý ngay với p_info (Chỉ dùng khi giỏ hàng trống)
        kws_price = ["giá", "bao nhiêu", "nhiêu tiền", "nhiêu", "rổ giá", "giá cả"]
        if any(kw in msg_norm for kw in kws_price):
            if p_info and not request.cart_items: # Elite V5.4: Skip sync price if cart has items
                logger.info("✅ [SupportAgent] Sync Heuristic HIT: PRICE_QUERY")
                final_reply = f"{debug_prefix}Dạ liệu trình **{p_info.name}** hiện tại có giá ưu đãi chỉ từ **{p_info.price_display}** ạ. 🌸 Anh/Chị muốn chốt số lượng bao nhiêu để Helen lên đơn ngay cho mình nhé?"
                await self._save_history(db, session_id, request.message, final_reply, SupportIntent.PRICE_QUERY, request.product_slug, customer_name)
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
                return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.PRICE_QUERY, session_id=session_id, status="DONE")
            else:
                logger.info("⚡ [SupportAgent] Sync Heuristic SKIP: Price query but Cart has items. Passing to Deep Brain.")

        # 3. INFO_ADDRESS & INFO_HOTLINE → Đọc từ Settings Cache
        is_address = any(kw in msg_norm for kw in ["địa chỉ", "ở đâu", "chi nhánh", "cửa hàng", "văn phòng", "trụ sở", "phòng khám", "showroom", "địa điểm", "chỗ nào"])
        is_hotline = any(kw in msg_norm for kw in ["điện thoại", "hotline", "số điện thoại", "liên hệ", "sốđt", "sdt", "website", "tư vấn qua đâu"])
        
        if is_address or is_hotline:
            logger.info("⚡ [SupportAgent] Sync Heuristic: Reading SystemSettings for ADDRESS/HOTLINE")
            raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
            if not raw_cfg:
                logger.warning("❌ [SupportAgent] Sync Heuristic MISS: primary_config cache empty")
                return None
            
            cfg = _json.loads(raw_cfg)
            ci = cfg.get("contact_info", {})
            
            if is_address:
                address = ci.get("address", "Chưa cập nhật địa chỉ")
                working_hours = ci.get("working_hours", "Chưa cập nhật")
                final_reply = f"{debug_prefix}Dạ địa chỉ của Micsmo ở **{address}** ạ. Giờ làm việc: {working_hours} 🌸."
                intent = SupportIntent.POLICY_QUERY
            else: # Hotline
                hotline = ci.get("hotline", "Chưa cập nhật hotline")
                final_reply = f"{debug_prefix}Dạ số hotline của Micsmo là **{hotline}** ạ. Anh/Chị cần tư vấn thêm cứ nhắn em nhé 🌸."
                intent = SupportIntent.POLICY_QUERY
                
            await self._save_history(db, session_id, request.message, final_reply, intent, request.product_slug, customer_name)
            await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
            return SupportResponse(ok=True, reply=final_reply, intent=intent, session_id=session_id, status="DONE")

        return None

support_agent = SupportAgentOperative()
