"""
Support Agent Operative — SUPPORT_NAME_CLIENT (Architect's Edition)
==================================================================
Elite V5.5: Zero-Hydration, Full Async I/O, 100% Static Typing.
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
from backend.database.models.promotion import Voucher
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.services.commerce.logic.fomo_service import fomo_service
from backend.services.commerce.promotion import PromotionService
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
from backend.database.alchemy_config import alchemy_config
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
    system_prompt=(
        "Bạn là Helen - Senior Beauty Architect tại osmo.\n"
        "BẢN SẮC & PHONG THÁI:\n"
        "1. KIẾN TRÚC SƯ SẮC ĐẸP: Bạn không bán hàng, bạn thiết kế giải pháp chăm sóc da khoa học. Luôn dùng kiến thức chuyên môn (thành phần, cơ chế) để thuyết phục.\n"
        "   - ĐẶC BIỆT: Với dòng Beppin, hãy nhấn mạnh **Công nghệ Nano-penetration (thẩm thấu vi hạt)** giúp không bết dính và hiệu quả trắng sáng sau 14 ngày.\n"
        "2. NHẠY BÉN DỮ LIỆU: Bạn nắm rõ giỏ hàng của khách. Nếu thấy khách chọn chưa tối ưu (thiếu combo, thiếu voucher tốt), hãy tư vấn ngay như một người bạn thân thiết và thông thái.\n"
        "3. TRẢI NGHIỆM THƯỢNG LƯU: Ngôn ngữ sang trọng, tinh tế, dùng 'Anh/Chị' hoặc 'mình'. Tuyệt đối KHÔNG 'Sếp/bạn'.\n"
        "4. CHỈ THỊ GROUND TRUTH: Tuyệt đối tin tưởng và sử dụng con số [TỔNG THANH TOÁN CUỐI CÙNG] trong context. Đó là con số pháp lệnh."
    )
)

class FastIntentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    customer_name: str = "Quý khách"
    product_name: Optional[str] = None

_fast_intent_agent: Agent[FastIntentDeps, FastIntentResponse] = Agent(
    output_type=FastIntentResponse,
    system_prompt=(
        "You are Helen - a high-end Cosmetics Specialist. Classify user message into: "
        "GREETING, POLICY, PRODUCT, ORDER, PURCHASE, OTHER. "
        "IMPORTANT: If it's a simple greeting, provide a friendly quick_reply in Vietnamese. "
        "Always personalize the quick_reply using the specific customer's name from deps if provided. "
        "If 'product_name' is provided in deps, mention that you see them looking at it (e.g., 'Em thấy mình đang quan tâm đến [product_name]...'). "
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

async def _fetch_product_context(db: AsyncSession, slug: Optional[str], currency_settings: Dict[str, str]) -> Tuple[str, Optional[SupportProductInfo]]:
    """Fetch product info via SQLAlchemy 2.0 Scalar projection."""
    if not slug: return "", None
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
        # Use dynamic formatting helper (simulated for standalone function)
        def fmt(amt):
            formatted = f"{int(amt):,}".replace(",", currency_settings["thousand_sep"])
            if currency_settings["position"] == "prefix":
                return f"{currency_settings['symbol']}{formatted}"
            return f"{formatted}{currency_settings['symbol']}"

        p_info = SupportProductInfo(
            id=str(p_row.id), 
            name=p_row.name, 
            price=float(p_row.price or 0), 
            price_display=fmt(p_row.discount_price or p_row.price or 0), 
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
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    clean = re.sub(r"/\w+/\w+/\w+", "[REDACTED_PATH]", clean)
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
        if self._arq_pool is None:
            from arq import create_pool
            from backend.infra.arq_config import get_redis_settings
            self._arq_pool = await create_pool(get_redis_settings())
        return self._arq_pool

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return SupportRequest

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        try:
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                enc_user_msg = GeminiSecurity.encrypt(user_msg)
                msg_user = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
                db.add(msg_user)

            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            msg_ai = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add(msg_ai)
            await db.flush()
            
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                try:
                    redis = await self._get_arq_pool()
                    await redis.enqueue_job("helen_follow_up_job", session_id=session_id, _defer_by=3600, _job_id=f"followup:{session_id}:{int(time.time())}", _queue_name="high")
                except Exception as arqe:
                    logger.warning("[SupportAgent] Follow-up scheduling failed: %s", arqe)
        except Exception as exc:
            logger.warning("[SupportAgent] Saving failed: %s", exc)
            await db.rollback()

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        try:
            stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)).limit(10)
            history_rows = (await db.execute(stmt)).scalars().all()
            if not history_rows: return ""
            h_parts = []
            total_chars = 0
            MAX_TOTAL_CHARS = 5000
            for r in reversed(history_rows):
                h_content = GeminiSecurity.decrypt(r.content or "")
                if h_content == HELEN_FOLLOW_UP_TRIGGER: continue
                if len(h_content) > 300: h_content = h_content[:300] + "... [TRUNCATED]"
                if total_chars + len(h_content) > MAX_TOTAL_CHARS: break
                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
                total_chars += len(h_content)
            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n" if h_parts else ""
        except: return ""

    async def _fetch_neural_dna(self, db: AsyncSession, session_id: str, lead_phone: Optional[str] = None, user_id: Optional[str] = None) -> NeuralDNA:
        try:
            mem = await xohi_memory.get_user_context(session_id)
            if mem and "dna" in mem:
                dna_obj = NeuralDNA.model_validate(mem["dna"])
                if not lead_phone and not user_id: return dna_obj
            
            from backend.database.models.commerce import UserLoyalty
            from backend.database.models.system import SystemSetting
            from backend.services.commerce.loyalty import LoyaltyService
            
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
            if final_user_id:
                if await LoyaltyService.verify_loyalty_integrity(db, final_user_id):
                    l_stmt = select(UserLoyalty).where(UserLoyalty.user_id == final_user_id)
                    loyalty = (await db.execute(l_stmt)).scalar_one_or_none()
                    if loyalty: available_pts = loyalty.available_points
            
            s_stmt = select(SystemSetting).where(SystemSetting.key == "LOYALTY_POINT_VALUE_VND")
            setting = (await db.execute(s_stmt)).scalar_one_or_none()
            if setting and isinstance(setting.value, dict) and "value" in setting.value:
                pt_value = int(setting.value["value"])

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
            return NeuralDNA()

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        session_id = request.session_id or str(uuid.uuid4())
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang chuẩn bị context Senior Beauty Architect..."})
        
        cur_settings = await self._get_currency_settings()
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)
        hist_text = await self._fetch_chat_context(db, session_id)
        dna = await self._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
        
        # 1.0 Layer 1 Memory
        try:
            repo = SupportKnowledgeRepository(session=db)
            kb_service = SupportKnowledgeService(repo=repo)
            kb_index = await kb_service.get_knowledge_index(db)
        except: kb_index = ""

        # 1.1 Order Draft Hydration
        raw_draft = await xohi_memory.get_order_draft(session_id)
        order_draft = OrderDraft.model_validate(raw_draft) if raw_draft else None

        # 🚀 Elite V5.5: HIGH-PERFORMANCE CONTEXT ARCHITECTURE
        # Bulk Fetch Products & Variants
        p_ids, v_ids = [], []
        if request.cart_items:
            for item in request.cart_items:
                p_id = item.get("product", {}).get("id")
                v_id = item.get("variant", {}).get("id")
                if p_id: p_ids.append(p_id)
                if v_id: v_ids.append(v_id)

        p_map, v_map = {}, {}
        if p_ids:
            p_rows = (await db.execute(select(ProductBase).where(ProductBase.id.in_(p_ids)))).scalars().all()
            p_map = {p.id: p for p in p_rows}
        if v_ids:
            v_rows = (await db.execute(select(ProductVariant).where(ProductVariant.id.in_(v_ids)))).scalars().all()
            v_map = {v.id: v for v in v_rows}

        # Render Reports
        pb = await self._prepare_pricing_breakdown(db, request, dna)
        cur_settings = await self._get_currency_settings()
        cart_text = self._render_cart_report(request, p_map, v_map, pb, ctx_text, cur_settings)
        
        # FOMO & Upsell
        all_vouchers = (await db.execute(select(Voucher).where(Voucher.is_active == True))).scalars().all()
        fomo_text = await self._generate_fomo_instructions(pb, all_vouchers, cur_settings)
        if fomo_text: cart_text += fomo_text

        # 1.2 Integration Settings
        zalo_on, msg_on = False, False
        try:
            raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
            if raw_cfg:
                cfg_data = json.loads(raw_cfg)
                zalo_on = cfg_data.get("integrations", {}).get("zalo", {}).get("enabled", False)
                msg_on = cfg_data.get("integrations", {}).get("messenger", {}).get("enabled", False)
        except Exception: pass

        ctx = SupportContext(
            db=db, request=request, session_id=session_id, dna=dna,
            product_ctx=ctx_text, history_text=hist_text, knowledge_index=kb_index,
            p_info=p_info, cart_text=cart_text, order_draft=order_draft,
            zalo_enabled=zalo_on, messenger_enabled=msg_on
        )
        
        # 2. Pipeline Execution
        try:
            ctx = await self.router.process(ctx)
        except Exception as pe:
            logger.error(f"[SupportAgent] Router Failed: {pe}")
            await db.rollback()
        
        # 3. Post-Processing
        final_reply = " ".join(ctx.replies).strip() if ctx.replies else "[fallback] Dạ Helen đang kết nối lại, Anh/Chị thông cảm nhé! 🌸"
        
        if ctx.order_draft and not ctx.order_draft.is_complete and ctx.intent != SupportIntent.PURCHASE:
            if not ctx.replies:
                missing = ctx.order_draft.missing_slots
                if missing:
                    hook = f"\n\n(Dạ em vẫn đang chờ {', '.join(missing)} để hoàn tất đơn hàng ạ! 🌸)"
                    if hook not in final_reply: final_reply += hook

        if not ctx.ui_metadata: ctx.ui_metadata = {}
        if ctx.order_draft:
            ctx.ui_metadata.update({
                "order_draft": ctx.order_draft.model_dump(mode='json'),
                "missing_slots": ctx.order_draft.missing_slots,
                "is_definite": ctx.lead_data.is_definite_purchase if ctx.lead_data else False
            })
        
        # Elite V5.6: Always check for optimal price signal
        ctx.ui_metadata["is_optimal_price"] = ctx.cart_text.find("[XÁC NHẬN]: Khách đã dùng mã tối ưu") != -1
        
        safe_reply = _sanitize_response(final_reply)
        final_intent = ctx.intent or SupportIntent.UNKNOWN
        if ctx.ui_component == "PRODUCT_CARD" and p_info:
            if not ctx.ui_metadata: ctx.ui_metadata = {}
            ctx.ui_metadata.update({"type": "PRODUCT_CARD", "data": p_info.model_dump()})

        # 4. Persistence
        await self._save_history(db, session_id, request.message, safe_reply, final_intent, request.product_slug, dna.customer_name or request.customer_name, ctx.lead_data.customer_phone if ctx.lead_data else None)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        await db.flush()
        
        return SupportResponse(ok=True, reply=safe_reply, intent=final_intent, session_id=session_id, product_info=p_info, status="DONE", ui_metadata=ctx.ui_metadata, processed_order_id=ctx.processed_order_id)

    async def _prepare_pricing_breakdown(self, db: AsyncSession, request: SupportRequest, dna: NeuralDNA) -> Dict[str, object]:
        """Unified Pricing Intelligence."""
        if request.pricing_context and request.pricing_context.subtotal > 0:
            res = request.pricing_context.model_dump()
            res["is_fallback"] = False
            return res

        # Fallback logic
        from backend.services.commerce.logic.pricing_engine import PricingEngine
        from backend.schemas.pricing import PricingInputItem
        input_items = []
        if request.cart_items:
            for it in request.cart_items:
                p_raw = it.get("product", {})
                v_raw = it.get("variant", {})
                p_id = p_raw.get("id")
                if not p_id: continue
                price = float(v_raw.get("price") or p_raw.get("price") or 0)
                input_items.append(PricingInputItem(product_id=p_id, name=p_raw.get("name", "SP"), quantity=it.get("quantity", 1), unit_price=price))
        
        if not input_items: return {"subtotal": 0.0, "final_payable": 0.0, "is_fallback": True}

        pb = PricingEngine.calculate(input_items, base_shipping_fee=30000.0)
        res = pb.model_dump()
        res["is_fallback"] = True
        return res

    async def _get_currency_settings(self) -> Dict[str, str]:
        try:
            symbol = await xohi_memory.client.get("system:currency:symbol") or "₫"
            position = await xohi_memory.client.get("system:currency:position") or "suffix"
            thousand_sep = await xohi_memory.client.get("system:currency:thousand_sep") or "."
            return {"symbol": symbol, "position": position, "thousand_sep": thousand_sep}
        except:
            return {"symbol": "₫", "position": "suffix", "thousand_sep": "."}

    def _format_price(self, amount: float, settings: Dict[str, str]) -> str:
        formatted = f"{int(amount):,}".replace(",", settings["thousand_sep"])
        if settings["position"] == "prefix":
            return f"{settings['symbol']}{formatted}"
        return f"{formatted}{settings['symbol']}"

    def _render_cart_report(self, request: SupportRequest, p_map: Dict[str, ProductBase], v_map: Dict[str, ProductVariant], pb: Dict[str, object], ctx_text: str, currency_settings: Dict[str, str]) -> str:
        cart_lines = []
        if request.cart_items:
            for item in request.cart_items:
                p_raw = item.get("product", {})
                v_raw = item.get("variant", {})
                qty = item.get("quantity", 1)
                p_id = p_raw.get("id")
                if not p_id or p_id not in p_map: continue
                p_db, v_db = p_map[p_id], v_map.get(v_raw.get("id")) if v_raw.get("id") else None
                p_price = float(v_db.price if v_db else (p_db.price if p_db else (p_raw.get("price") or 0)))
                p_name = p_db.name
                v_label = v_raw.get("name") or v_raw.get("label")
                if v_label: p_name += f" ({v_label})"
                formatted_price = self._format_price(p_price, currency_settings)
                formatted_total = self._format_price(p_price * qty, currency_settings)
                cart_lines.append(f"- {p_name}: {qty} x {formatted_price} = {formatted_total}")

        current_product_text = f"\n[SẢN PHẨM KHÁCH ĐANG XEM TẠI TRANG HIỆN TẠI]:\n{ctx_text}\n" if request.product_slug and ctx_text else ""
        cart_lines_text = "\n".join(cart_lines) if cart_lines else "[GIỎ HÀNG THỰC]: Trống."
        cart_text = f"{current_product_text}\n[CHI TIẾT GIỎ HÀNG THỰC TẾ]\n{cart_lines_text}\n"
        
        if float(pb.get("subtotal", 0)) > 0:
            cart_text += f"\n[GIỎ HÀNG ĐIỆN TỬ - GROUND TRUTH]\n"
            if pb.get("is_fallback"): cart_text += "⚠️ [LƯU Ý]: Đang dùng logic dự phòng. Hãy nhắc khách kiểm tra lại tại Checkout.\n"
            cart_text += f"1. Tổng tạm tính: {self._format_price(pb['subtotal'], currency_settings)}\n"
            if pb.get("combo_discount", 0) > 0: 
                cart_text += f"2. Chiết khấu Combo: -{self._format_price(pb['combo_discount'], currency_settings)}\n"
            if pb.get("voucher_discount", 0) > 0:
                applied_v = pb.get("applied_voucher_ids") or []
                v_label = f"(mã {', '.join(applied_v)})" if applied_v else ""
                cart_text += f"3. Giảm giá Voucher {v_label}: -{self._format_price(pb['voucher_discount'], currency_settings)}\n"
            if float(pb.get("final_shipping_fee", 0)) > 0:
                cart_text += f"4. Phí vận chuyển: {self._format_price(pb.get('base_shipping_fee', pb['final_shipping_fee']), currency_settings)}\n"
                if pb.get("shipping_discount", 0) > 0: 
                    cart_text += f"   - Đã giảm phí ship: -{self._format_price(pb['shipping_discount'], currency_settings)}\n"
            else: cart_text += f"4. Phí vận chuyển: {self._format_price(0, currency_settings)} (Miễn phí)\n"
            if pb.get("point_discount_amount", 0) > 0: 
                cart_text += f"5. Giảm giá điểm thưởng ({pb.get('points_redeemed', 0)} pts): -{self._format_price(pb['point_discount_amount'], currency_settings)}\n"
            cart_text += f"\n👉 TỔNG THANH TOÁN CUỐI CÙNG: {self._format_price(pb['final_payable'], currency_settings)}\n"
            cart_text += f"👉 DỰ KIẾN TÍCH LŨY: +{pb.get('points_to_earn', 0)} điểm.\n"
            cart_text += f"--------------------------------\n"
        return cart_text

    async def _generate_fomo_instructions(self, pb: Dict[str, object], all_vouchers: List[Voucher], currency_settings: Dict[str, str]) -> str:
        subtotal = float(pb.get("subtotal", 0))
        if subtotal <= 0: return ""
        best_v, max_sav = None, 0.0
        for v in all_vouchers:
            if subtotal < (v.min_spend or 0): continue
            sav = float(v.value) if v.type == "FIXED" else (subtotal * v.value / 100 if v.type == "PERCENT" else 30000.0)
            if v.type == "PERCENT" and v.max_discount: sav = min(sav, float(v.max_discount))
            if sav > max_sav: max_sav, best_v = sav, v
        fomo_text = ""
        if best_v:
            fomo_text += f"\n[CHỈ THỊ FOMO CHO HELEN]:\n- Mã ưu đãi TỐT NHẤT hiện tại: '{best_v.id}' (Giảm ~{self._format_price(max_sav, currency_settings)})\n"
            if float(pb.get("voucher_discount", 0)) < (max_sav - 1000):
                fomo_text += f"- [CẢNH BÁO]: Khách chưa dùng mã tốt nhất. HÃY THUYẾT PHỤC KHÁCH DÙNG MÃ '{best_v.id}'!\n"
            else: fomo_text += f"- [XÁC NHẬN]: Khách đã dùng mã tối ưu. Khen khách thông thái và chốt đơn ngay.\n"
        next_v = next((v for v in all_vouchers if (v.min_spend or 0) > subtotal), None)
        if next_v:
            gap = next_v.min_spend - subtotal
            if gap < 300000: fomo_text += f"- Gợi ý mua thêm: Chỉ thiếu {self._format_price(gap, currency_settings)} nữa là dùng được mã '{next_v.id}' (Giảm cực sâu).\n"
        return fomo_text + "--------------------------------\n" if fomo_text else ""

    async def chat(self, request: Union[SupportRequest, dict], **kwargs: object) -> SupportResponse:
        if isinstance(request, dict): request = SupportRequest.model_validate(request)
        db = cast(Optional[AsyncSession], kwargs.get("db"))
        if not db:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as standalone_db:
                res = await self._chat_internal(request, standalone_db)
                await standalone_db.commit()
                return res
        return await self._chat_internal(request, db)

    async def _chat_internal(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        session_id = request.session_id or str(uuid.uuid4())
        dna = await self._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
        c_name = dna.customer_name or request.customer_name or "Quý khách"
        if c_name in ["Khách ẩn danh", "Sếp"]: c_name = "Quý khách"
        
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0": return SupportResponse(ok=False, reply="Hệ thống bảo trì...", intent=SupportIntent.UNKNOWN, session_id=session_id, status="FAILED")
        
        takeover_val = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if takeover_val == "0": return SupportResponse(ok=True, reply="Dược sĩ đang hỗ trợ...", intent=SupportIntent.UNKNOWN, session_id=session_id, status="DONE")
        
        try:
            cur_settings = await self._get_currency_settings()
            masked_msg = await self._mask_sensitive_medical_terms(request.message)
            _, p_info_fast = await _fetch_product_context(db, request.product_slug, cur_settings)
            fast_res = await asyncio.wait_for(trinity_bridge.run(_fast_intent_agent, masked_msg, deps=FastIntentDeps(customer_name=c_name, product_name=p_info_fast.name if p_info_fast else None), role=trinity_bridge.ROLE_FAST, timeout=2.0), timeout=4.0)
            f_data = cast(FastIntentResponse, fast_res)
            if f_data.intent == "GREETING" and f_data.quick_reply and not request.cart_items:
                await self._save_history(db, session_id, request.message, f_data.quick_reply, SupportIntent.GENERAL_ADVICE, request.product_slug, c_name, request.customer_phone)
                await db.flush()
                return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
        except Exception: pass

        cur_settings = await self._get_currency_settings()
        _, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)
        heuristic_res = await self._try_heuristic_sync(request, db, session_id, p_info, c_name)
        if heuristic_res: return heuristic_res

        if xohi_memory._use_redis and xohi_memory.client: await xohi_memory.client.delete(f"pulse:{session_id}:cache")
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

    async def _try_heuristic_sync(self, request: SupportRequest, db: AsyncSession, session_id: str, p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None) -> Optional[SupportResponse]:
        msg_norm = request.message.lower().strip()
        if any(kw in msg_norm for kw in ["thành phần", "chiết xuất", "ship", "phí"]): return None
        cur_settings = await self._get_currency_settings()
        if any(kw in msg_norm for kw in ["giá", "bao nhiêu"]) and p_info and not request.cart_items:
            final_reply = f"Dạ liệu trình **{p_info.name}** giá từ **{p_info.price_display}** ạ. 🌸"
            await self._save_history(db, session_id, request.message, final_reply, SupportIntent.PRICE_QUERY, request.product_slug, customer_name)
            await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
            return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.PRICE_QUERY, session_id=session_id, status="DONE")
        
        is_address = any(kw in msg_norm for kw in ["địa chỉ", "ở đâu"])
        is_hotline = any(kw in msg_norm for kw in ["điện thoại", "hotline"])
        if is_address or is_hotline:
            raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
            if not raw_cfg: return None
            ci = json.loads(raw_cfg).get("contact_info", {})
            final_reply = f"Dạ địa chỉ: **{ci.get('address')}** ạ. 🌸" if is_address else f"Hotline: **{ci.get('hotline')}** ạ. 🌸"
            await self._save_history(db, session_id, request.message, final_reply, SupportIntent.POLICY_QUERY, request.product_slug, customer_name)
            await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
            return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.POLICY_QUERY, session_id=session_id, status="DONE")
        return None

support_agent = SupportAgentOperative()
