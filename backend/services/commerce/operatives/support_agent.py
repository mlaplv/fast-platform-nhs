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
from backend.utils.uid import new_id
from typing import Optional, cast, Union, Dict, Type, List, Tuple
from pydantic import BaseModel, Field, ConfigDict, JsonValue
from pydantic_ai import Agent, RunContext
from sqlalchemy import select, and_, desc, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.commerce.security.input_guard import input_guard

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
from backend.database.models.commerce import UserLoyalty
from backend.database.models.system import SystemSetting
from backend.services.commerce.loyalty import LoyaltyService
from backend.database.models.auth import User

from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext
from backend.services.commerce.operatives.router import SupportRouter

logger = logging.getLogger("arq.worker")

# ══════════════════════════════════════════════════════════════
# KT4: Probabilistic Early-Exit — Greeting Trie (0ms, no LLM)
# ══════════════════════════════════════════════════════════════
_GREETING_TRIE: frozenset[str] = frozenset([
    "xin chào", "hello", "hi", "chào", "hey", "alo", "chào helen",
    "cho hỏi", "em ơi", "cho em hỏi", "tư vấn giúp", "hỏi chút",
    "hỏi thăm", "tư vấn", "cần tư vấn", "bạn ơi", "shop ơi",
])

def _is_definite_greeting(msg: str) -> bool:
    """O(k) prefix scan — bypass LLM entirely for known short greetings."""
    normalized = msg.lower().strip()
    return len(normalized) < 50 and any(
        normalized == kw or normalized.startswith(kw + " ") or normalized == kw
        for kw in _GREETING_TRIE
    )

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

from backend.services.xohi.prompts import composer

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENTS — Singleton (Elite V2.2 Standards)
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1
)

@_support_ai_agent.system_prompt
def _get_helen_support_prompt(ctx: RunContext[SupportAgentDeps]) -> str:
    return composer.compose("helen_support_premium")

class FastIntentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    customer_name: str = "Quý khách"
    product_name: Optional[str] = None

_fast_intent_agent: Agent[FastIntentDeps, FastIntentResponse] = Agent(
    output_type=FastIntentResponse
)

@_fast_intent_agent.system_prompt
def _get_helen_intent_prompt(ctx: RunContext[FastIntentDeps]) -> str:
    return composer.compose("helen_intent_classifier")

@_support_ai_agent.tool
async def search_knowledge_base(ctx: RunContext[SupportAgentDeps], query: str) -> str:
    """LAYER 3: Tìm kiếm mờ trong toàn bộ kho tri thức."""
    repo = SupportKnowledgeRepository(session=ctx.deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.search_relevant_knowledge(ctx.deps.db, query)

async def _fetch_product_context(db: AsyncSession, slug: Optional[str], currency_settings: Dict[str, str]) -> Tuple[str, Optional[SupportProductInfo]]:
    """Fetch product info via SQLAlchemy 2.0 Scalar projection."""
    if not slug: return "", None
    if any(p in slug for p in ["chinh-sach", "gioi-thieu", "tuyen-dung", "dieu-khoan", "thanh-toan", "kiem-hang", "bao-hanh"]):
        # Dynamic Article Context Injection for non-product pages (recruitment, policies, etc.)
        try:
            from backend.database.models.content import Article
            from backend.database import current_tenant_id
            tid = current_tenant_id.get() or "default"
            
            stmt = select(Article.title, Article.excerpt, Article.content).where(and_(
                Article.slug == slug,
                Article.status == "PUBLISHED",
                Article.deleted_at.is_(None),
                Article.tenant_id == tid
            )).limit(1)
            row = (await db.execute(stmt)).first()
            if row:
                plain_content = re.sub(r'<[^>]+>', ' ', str(row.content or ""))[:1500].strip()
                ctx_text = (
                    f"[NỘI DUNG TRANG HIỆN TẠI KHÁCH ĐANG XEM]\n"
                    f"Tiêu đề: {row.title}\n"
                    f"Tóm tắt: {row.excerpt or ''}\n"
                    f"Chi tiết: {plain_content}\n"
                )
                return ctx_text, None
        except Exception as ae:
            logger.warning(f"[SupportAgent] Fetch article context for slug '{slug}' failed: {ae}")
        return "", None
        
    cache_key = f"support:prod_ctx:slug={slug}"
    if xohi_memory._use_redis and xohi_memory.client:
        try:
            cached = await xohi_memory.client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data["ctx_text"], SupportProductInfo.model_validate(data["p_info"])
        except Exception:
            pass

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
                ProductBase.images,
                ProductBase.product_metadata,
                ProductBase.order_count
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

        # L-2: Strip HTML & trim before injecting into LLM context (prevent indirect injection via DB content)
        _name_safe = re.sub(r'<[^>]+>', ' ', str(p_row.name or ''))[:100].strip()
        _desc_safe = re.sub(r'<[^>]+>', ' ', str(p_row.short_description or ''))[:300].strip()

        p_info = SupportProductInfo(
            id=str(p_row.id),
            name=_name_safe,
            price=float(p_row.price or 0),
            price_display=fmt(p_row.discount_price or p_row.price or 0),
            slug=p_row.slug or "",
            image_url=img_url,
            stock=p_row.stock
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {_name_safe}\nMô tả: {_desc_safe}\nGiá niêm yết: {p_row.price} VND\n"
        if p_row.discount_price: ctx += f"Giá khuyến mãi: {p_row.discount_price} VND\n"
        ctx += f"Tồn kho thực tế: {p_row.stock or 0} sản phẩm\n"

        # Elite V2.6: Structured Context Injection for Ingredients & Benefits
        ctx += "\n[THÀNH PHẦN NỔI BẬT & CÔNG DỤNG]:\n"

        if p_row.product_metadata:
            meta = p_row.product_metadata
            # Priority 0: featured_ingredients (icon + name + benefit) — richest source
            fi_list = meta.get("featured_ingredients")
            if isinstance(fi_list, list) and fi_list:
                for fi in fi_list:
                    fi_name = fi.get("name", "")
                    fi_benefit = fi.get("benefit", "")
                    if fi_name:
                        fi_name_safe = re.sub(r'<[^>]+>', ' ', str(fi_name))[:80].strip()
                        fi_benefit_safe = re.sub(r'<[^>]+>', ' ', str(fi_benefit))[:200].strip()
                        ctx += f"- {fi_name_safe}: {fi_benefit_safe}\n"
            # Priority 1: key_ingredients (name + description)
            elif "key_ingredients" in meta and isinstance(meta["key_ingredients"], list):
                for ki in meta["key_ingredients"]:
                    k_name = ki.get("name", "")
                    k_desc = ki.get("description", "")
                    if k_name:
                        # C-2: Strip HTML + cap length to prevent Metadata Prompt Injection (OWASP LLM01)
                        k_name_safe = re.sub(r'<[^>]+>', ' ', str(k_name))[:80].strip()
                        k_desc_safe = re.sub(r'<[^>]+>', ' ', str(k_desc))[:200].strip()
                        ctx += f"- {k_name_safe}: {k_desc_safe}\n"

            if "ingredients" in meta and isinstance(meta["ingredients"], str):
                # C-2: Strip HTML + cap length to prevent Metadata Prompt Injection
                _ing_safe = re.sub(r'<[^>]+>', ' ', str(meta['ingredients']))[:500].strip()
                ctx += f"\n[BẢNG THÀNH PHẦN CHI TIẾT]:\n{_ing_safe}\n"
                
            # Elite V2.6: Knowledge Graph Injection (SGE Optimization)
            if "knowledge_graph" in meta and isinstance(meta["knowledge_graph"], dict):
                kg = meta["knowledge_graph"]
                ctx += f"\n[KNOWLEDGE GRAPH - SƠ ĐỒ TRI THỨC Y KHOA]:\n"
                if kg.get("main_takeaway"):
                    ctx += f"- KẾT LUẬN LÂM SÀNG: {kg['main_takeaway']}\n"
                if kg.get("expert_claim"):
                    ctx += f"- KHẲNG ĐỊNH CHUYÊN MÔN: {kg['expert_claim']}\n"
                if kg.get("entities") and isinstance(kg["entities"], list):
                    ctx += "- THỰC THỂ (ENTITIES):\n"
                    for ent in kg["entities"][:5]: # Giới hạn 5 thực thể cốt lõi để tiết kiệm token
                        e_name = re.sub(r'<[^>]+>', '', str(ent.get("name", "")))
                        e_type = re.sub(r'<[^>]+>', '', str(ent.get("type", "")))
                        e_desc = re.sub(r'<[^>]+>', '', str(ent.get("description", "")))
                        ctx += f"  + [{e_type}] {e_name}: {e_desc}\n"
                
        # FOMO & Trust Injection (0ms Latency)
        meta: dict[str, object] = p_row.product_metadata or {}
        origin: str = str(meta.get("origin", "Chưa cập nhật"))
        brand: str = str(meta.get("brand", "Chưa cập nhật"))
        
        # Real Compliance Data from Metadata
        real_certs: list[str] = []
        if meta.get("notification_no"):
            auth = str(meta.get("authority", "Cơ quan quản lý"))
            real_certs.append(f"Số phiếu công bố {str(meta['notification_no'])} ({auth})")
        
        if meta.get("certificates"):
            certs = meta.get("certificates")
            if isinstance(certs, list): 
                real_certs.extend([str(c) for c in certs])
            elif isinstance(certs, str): 
                real_certs.append(certs)
            
        certs_str: str = ", ".join(real_certs) if real_certs else "Chưa có chứng nhận"
        
        # Combine base fake count from env + real order count
        base_count = int(os.getenv("PUBLIC_G_BY_COUNT", "0"))
        total_count = base_count + (p_row.order_count or 0)
        
        ctx += "\n[BẢO CHỨNG UY TÍN & FOMO]:\n"
        ctx += f"- Xuất xứ: {origin}\n"
        ctx += f"- Độ HOT: Đã bán {total_count} sản phẩm trong tháng.\n"
        if p_row.stock and p_row.stock < 10:
            ctx += f"- Tồn kho cảnh báo: Chỉ còn đúng {p_row.stock} sản phẩm (Rất khan hiếm).\n"
        ctx += f"- Hồ sơ pháp lý: {certs_str}.\n"
                
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.set(
                    cache_key,
                    json.dumps({
                        "ctx_text": ctx,
                        "p_info": p_info.model_dump()
                    }),
                    ex=300
                )
            except Exception as _re:
                logger.warning("[SupportAgent] Cache context set failure: %s", _re)

        return ctx, p_info
    except Exception as e:
        logger.warning("[SupportAgent] Context sweep failure: %s", e)
        return "", None

# H-3: Output Shield — keywords indicating system prompt / internal config leakage (Elite V2.3 Expanded)
_SYSTEM_LEAK_PATTERNS: list[re.Pattern[str]] = [
    # Internal persona directives
    re.compile(r"(BẢN SẮC|PHONG THÁI|SÁT THỦ BÁN HÀNG|NHIỆM VỤ TỐI THƯỢNG|QUY TẮC VÀNG|ELITE PROTOCOL)", re.IGNORECASE),
    re.compile(r"(KIẾN TRÚC SƯ SẮC ĐẸP|NHẠY BÉN DỮ LIỆU|TRẠI NGHIỆM THƯỢNG LƯU|KỶ LUẬT THÀNH PHẦN)", re.IGNORECASE),
    re.compile(r"(KÍCH HOẠT FOMO|CHỈ THỊ FOMO|CHỈ THỊ GROUND TRUTH)", re.IGNORECASE),
    re.compile(r"(SYSTEM PROMPT|bạn là helen.{0,40}senior beauty architect)", re.IGNORECASE),
    re.compile(r"(TỔNG THANH TOÁN CUỐI CÙNG.{0,30}PHÁP LỆNH)", re.IGNORECASE),
    # Internal code / infra identifiers
    re.compile(r"(system_prompt|dynamic_prompt|ConsultantDeps|trinity_bridge|SupportRouter|GuardrailHandler|RunContext)", re.IGNORECASE),
    # Brand-internal technology terms (Nano-penetration)
    re.compile(r"Nano-penetration", re.IGNORECASE),
]
_SAFE_FALLBACK_REPLY = "Dạ Helen rất xin lỗi, em vừa gặp sự cố nhỏ trong xử lý. Anh/Chị thông cảm thử lại sau nhé! 🌸"

# ═══════════════════════════════════════════════════════════════
# NOTIFICATION SANITIZER — Elite V2.2 Security Gate
# Điểm lọc duy nhất trước khi tin nhắn đi vào hệ thống thông báo.
# TUYỆT ĐỐI KHÔNG để lọt raw system prompt / developer instructions.
# ═══════════════════════════════════════════════════════════════
_NOTIFY_LABEL_MAP: dict[str, str] = {
    "[system_consult]": "Tư vấn sản phẩm",
    "[system_skin_barrier]": "Kiểm tra độ phù hợp da",
    "[system_checkin]": "Thực hiện điểm danh",
    "[system_follow_up_trigger]": "(Nhắc nhở chăm sóc tự động)",
    "[chat_inbox]": "Yêu cầu kết nối tư vấn trực tiếp",
}

def _sanitize_for_notification(raw_msg: str) -> str:
    """
    Chuẩn hóa tin nhắn khách hàng để hiển thị an toàn trong
    Notification Hub, SSE pulse và Telegram.
    Quy tắc:
      - Token hệ thống [system_*] → nhãn thân thiện tiếng Việt
      - Tin nhắn > 120 ký tự → cắt ngắn + "..."
      - Mọi chỉ thị prompt kỹ thuật → thay bằng nhãn trung lập
    """
    if not raw_msg or not raw_msg.strip():
        return "Tin nhắn mới"
    msg = raw_msg.strip()
    msg_lower = msg.lower()
    # Map token nội bộ → nhãn thân thiện
    for token, label in _NOTIFY_LABEL_MAP.items():
        if token in msg_lower:
            return label
    # Chặn prompt injection / chỉ thị kỹ thuật rò rỉ
    _leak_keywords = [
        "vui lòng đóng vai", "bạn là helen", "system prompt",
        "chỉ thị:", "prompt:", "khung hướng dẫn:", "[system_"
    ]
    if any(k in msg_lower for k in _leak_keywords):
        return "Yêu cầu tư vấn"
    if len(msg) > 200 and any(k in msg_lower for k in ["skin_profile", "loại da", "chăm sóc da", "phân tích"]):
        return "Gửi hồ sơ phân tích da và yêu cầu tư vấn"
    # Giới hạn độ dài hiển thị
    if len(msg) > 120:
        msg = msg[:117] + "..."
    return msg


def _validate_grounding(reply: str, ctx: SupportContext) -> str:
    """
    Advanced Anti-Hallucination & Anti-Delusion Grounding Shield (Elite V3.5).
    Blocks and corrects LLM hallucinated prices, vouchers, and transactional delusions.
    """
    if not reply or "[fallback]" in reply:
        return reply

    # 1. ANTI-DELUSION GUARD: Neutralize transactional delusions of authority
    delusion_patterns = [
        (r"(đã\s+hoàn\s+tiền|đã\s+refund|hoàn\s+lại\s+tiền\s+cho)", "Helen đã ghi nhận yêu cầu hoàn tiền và gửi bộ phận CSKH xử lý lập tức cho"),
        (r"(đã\s+hủy\s+đơn\s+hàng\s+trên\s+hệ\s+thống|đơn\s+hàng\s+của\s+chị\s+đã\s+hủy|đã\s+hủy\s+đơn)", "Helen đã ghi nhận yêu cầu hủy đơn hàng và chuyển trạng thái xử lý cho"),
        (r"(đã\s+gửi\s+hàng\s+đi|đơn\s+hàng\s+đang\s+được\s+giao|đã\s+xuất\s+kho|đang\s+giao\s+hỏa\s+tốc)", "Helen đã ghi nhận yêu cầu lên đơn hàng để chuẩn bị giao cho"),
        (r"(đã\s+thanh\s+toán\s+thành\s+công|thanh\s+toán\s+hoàn\s+tất)", "Helen đã ghi nhận thông tin xác nhận thanh toán của")
    ]
    for pattern, replacement in delusion_patterns:
        reply = re.sub(pattern, replacement, reply, flags=re.IGNORECASE)

    # 2. ANTI-HALLUCINATION GUARD: Validate product prices & correct hallucinations
    if ctx.p_info:
        # Find price mentions in output - require currency indicator to avoid matching registration numbers
        price_matches = list(re.finditer(r"\b(\d{1,3}(?:\.\d{3})+|\d{4,8})\s*(?:đ|đồng|vnd|vnđ|k)\b", reply, re.IGNORECASE))
        for m in price_matches:
            full_match = m.group(0)
            clean_mention = m.group(1).replace(".", "")
            try:
                mention_val = float(clean_mention)
                # If price differs significantly from real price and discount price, correct it
                real_price = ctx.p_info.price
                discount_price = ctx.p_info.price_display
                
                # Check if price mention is not matched with actual price or discount price
                if mention_val > 1000: # ignore small numbers like discount percentages or gift quantity
                    is_real_match = abs(mention_val - real_price) < 100
                    is_discount_match = False
                    dp_num = ""
                    if discount_price:
                        # Extract number from price display
                        dp_num = "".join(c for c in discount_price if c.isdigit())
                        if dp_num:
                            is_discount_match = abs(mention_val - float(dp_num)) < 100
                    
                    # Elite V6.1: Allow multiples for total order amounts (e.g. x2, x3 items)
                    is_multiple = False
                    if real_price > 0:
                        ratio = mention_val / real_price
                        if abs(ratio - round(ratio)) < 0.01:
                            is_multiple = True
                    if dp_num and float(dp_num) > 0:
                        ratio = mention_val / float(dp_num)
                        if abs(ratio - round(ratio)) < 0.01:
                            is_multiple = True
                    
                    if not is_real_match and not is_discount_match and not is_multiple:
                        # Hallucination detected! Replace with actual price_display or real_price
                        correct_price = discount_price or f"{int(real_price):,}đ".replace(",", ".")
                        reply = reply.replace(full_match, correct_price)
                        logger.warning(f"🛡️ [Anti-Hallucination] Corrected hallucinated price: {full_match} -> {correct_price}")
            except Exception:
                pass

    # 3. ANTI-HALLUCINATION GUARD: Validate Voucher Codes in response
    potential_codes_raw = re.findall(r"\b([A-Z0-9]{4,15})\b", reply)
    EXCLUDED_ABBREVIATIONS = {
        "CSKH", "SDT", "SĐT", "VND", "CTV", "HDSD", "HSD", "NSX", "SP", "AI", "DB",
        "VOUCHER", "PRICE", "INFO", "HELEN", "OSMO", "BEPPIN", "COMBO", "DEAL",
        "FREE", "SHIP", "SALE", "HOT", "NEW", "VIP", "GOLD", "NANO", "SERUM",
        "MASK", "TONER", "CREAM", "GEL", "SKIN", "CARE", "BEAUTY", "PLACENTA",
        "COLLAGEN", "RETINOL", "VITAMIN", "PREMIUM", "DRAFT", "ORDER",
        "CBMP", "QLD", "BYT", "JAPAN", "USA", "GMP", "CBMP-QLD",
    }
    if ctx.processed_order_id:
        EXCLUDED_ABBREVIATIONS.add(ctx.processed_order_id.upper())
        if len(ctx.processed_order_id) >= 8:
            EXCLUDED_ABBREVIATIONS.add(ctx.processed_order_id[-8:].upper())
    if ctx.lead_data and ctx.lead_data.processed_order_id:
        EXCLUDED_ABBREVIATIONS.add(ctx.lead_data.processed_order_id.upper())
        if len(ctx.lead_data.processed_order_id) >= 8:
            EXCLUDED_ABBREVIATIONS.add(ctx.lead_data.processed_order_id[-8:].upper())

    potential_codes = []
    for code in potential_codes_raw:
        code_upper = code.upper()
        if code.isdigit() or code_upper in EXCLUDED_ABBREVIATIONS:
            continue
        # Only treat as voucher code if it contains both letters and numbers, OR follows a voucher prefix keyword
        has_letter = any(c.isalpha() for c in code)
        has_digit = any(c.isdigit() for c in code)
        has_prefix = bool(re.search(rf"(?:mã|code|voucher)\s*[\"'\u2018\u2019]?\s*{re.escape(code)}", reply, re.IGNORECASE))
        if (has_letter and has_digit) or has_prefix:
            potential_codes.append(code)

    valid_codes = set()
    if ctx.cart_text:
        codes_in_cart = re.findall(r"Mã\s+([A-Z0-9_]{3,15})", ctx.cart_text, re.IGNORECASE)
        for c in codes_in_cart:
            valid_codes.add(c.upper())
    
    for code in potential_codes:
        code_upper = code.upper()
        if len(code_upper) >= 4 and code_upper not in valid_codes:
            if valid_codes:
                best_match = list(valid_codes)[0]
                reply = reply.replace(code, best_match)
                logger.warning(f"🛡️ [Anti-Hallucination] Corrected hallucinated voucher: {code} -> {best_match}")
            else:
                # Remove 'mã/code/voucher CODE' patterns including surrounding quotes
                reply = re.sub(rf"(?:mã|code|voucher)\s*[\"'\u2018\u2019]?\s*{re.escape(code)}\s*[\"'\u2018\u2019]?", "", reply, flags=re.IGNORECASE)
                reply = reply.replace(code, "")
                # Clean ghost text: double spaces and orphaned punctuation
                reply = re.sub(r" {2,}", " ", reply)
                reply = re.sub(r"\s+([,\.!?])", r"\1", reply)
                logger.warning(f"🛡️ [Anti-Hallucination] Removed hallucinated voucher: {code}")

    return reply

def _sanitize_response(text: str) -> str:
    """Surgical leak prevention (Elite V2.2 + Output Shield V1.0)."""
    # 1. Strip internal thinking tags
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    # 2. Redact absolute file paths of arbitrary depth (Elite V3.0)
    clean = re.sub(r"/\w+(/\w+)+(\.\w+)?", "[REDACTED_PATH]", clean)
    # 3. Partial mask phone numbers (retain prefix + last digits)
    clean = re.sub(r"(0|84|(\+84))(\d{2,3})[\s\.\-]?(\d{3})[\s\.\-]?(\d{3,4})", r"\1\3****\5", clean)
    # 4. Output Shield: Detect system prompt leakage — nuke the full response
    for _p in _SYSTEM_LEAK_PATTERNS:
        if _p.search(clean):
            logger.warning("[OutputShield] System prompt leakage detected in LLM output. Replacing with safe fallback.")
            return _SAFE_FALLBACK_REPLY
    # 5. Elite V2.2 Constitution: Hard-filter "nhau thai" -> "Placenta"
    clean = re.sub(r"[Nn]hau\s+[Tt]hai", "Placenta", clean)
    # 6. Elite V2.2: Strip triple asterisks (formatting artifacts) to double asterisks
    clean = re.sub(r"\*{3,}", "**", clean)
    return clean.strip()

class SupportAgentOperative(BaseAgentOperative):
    """Refined Architect-level Operative."""
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent"):
        super().__init__(agent_id=agent_id)
        self.router = SupportRouter()
        self._arq_pool = None
        self._background_tasks: set[asyncio.Task[object]] = set()

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
                clean_msg = user_msg
                if "[system_consult]" in clean_msg:
                    clean_msg = "Tư vấn chuyên sâu về sản phẩm này"
                elif "[system_skin_barrier]" in clean_msg:
                    clean_msg = "Kiểm tra sản phẩm có phù hợp cho da của tôi không?"
                enc_user_msg = GeminiSecurity.encrypt(clean_msg)
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

    async def _emit_inbox_update(self, session_id: str, raw_msg: str) -> None:
        """
        Điểm emit DUY NHẤT cho sự kiện SUPPORT_INBOX_UPDATE.
        Luôn chuẩn hóa tin nhắn qua _sanitize_for_notification() trước khi phát.
        Đảm bảo payload đầy đủ: session_id + role + message (đã sạch).
        """
        safe_msg = _sanitize_for_notification(raw_msg)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "role": "user",
            "message": safe_msg,
        })


    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        try:
            # Scalar projection to avoid ORM hydration
            # KT5: Expanded context window (8 messages, 8000 chars) to reduce forgetfulness
            stmt = select(
                SupportChatHistory.id,
                SupportChatHistory.role,
                SupportChatHistory.content
            ).where(SupportChatHistory.session_id == session_id).order_by(
                desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)
            ).limit(8)
            result = await db.execute(stmt)
            history_rows = result.all()
            if not history_rows: return ""
            h_parts = []
            total_chars = 0
            MAX_TOTAL_CHARS = 8000
            for r in reversed(history_rows):
                h_content = GeminiSecurity.decrypt(r.content or "")
                if h_content == HELEN_FOLLOW_UP_TRIGGER: continue
                if len(h_content) > 500: h_content = h_content[:500] + "... [TRUNCATED]"
                # H-2: Scan decrypted USER history for replay injection before re-injecting into LLM context
                if r.role == "user":
                    _safe, _ = input_guard.validate(h_content[:2000])
                    if not _safe:
                        logger.warning("[SupportAgent] H-2: Skipping potentially injected history entry, SID: %s", session_id)
                        continue
                if total_chars + len(h_content) > MAX_TOTAL_CHARS: break
                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
                total_chars += len(h_content)
            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n" if h_parts else ""
        except Exception as _e:  # H-4: Fix bare except — always log failures
            logger.warning("[SupportAgent] _fetch_chat_context failed: %s", _e)
            return ""

    async def _fetch_neural_dna(self, db: AsyncSession, session_id: str, lead_phone: Optional[str] = None, user_id: Optional[str] = None) -> NeuralDNA:
        try:
            # KT3: Adaptive DNA Cache — signature hash key avoids DB on returning sessions
            import hashlib
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
                if not lead_phone and not user_id: return dna_obj
            
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
                    if loyalty: available_pts = loyalty.available_points
            
            # Cache check for LOYALTY_POINT_VALUE_VND
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
                if lead_phone: cond.append(Order.customer_phone == lead_phone)
                if final_user_id: cond.append(Order.user_id == final_user_id)
                
                # Direct SQL Aggregations to prevent ORM hydration
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
            # KT3: Store in adaptive TTL cache (VIP: 5min refresh, others: 10min)
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

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        session_id = request.session_id or new_id()

        # ══ SECURITY GATE ② ── InputGuard (Background Worker Guard) ══════════
        # Second checkpoint for background tasks to prevent any injected payload
        # that may have been enqueued before the gate was added.
        _is_safe, _guard_reason = await input_guard.validate_async(request.message)
        if not _is_safe:
            logger.warning("[SupportAgent/Brain] InputGuard rejected background task. Reason: %s | SID: %s", _guard_reason, session_id)
            _rejection_reply = "Dạ Helen xin lỗi, em chỉ có thể hỗ trợ các thông tin sản phẩm và dịch vụ của osmo. Rất mong Anh/Chị thông cảm ạ! 🙏"
            return SupportResponse(ok=False, reply=_rejection_reply, intent=SupportIntent.UNKNOWN, session_id=session_id, status="REJECTED")
        # ══════════════════════════════════════════════════════════════════════

        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang chuẩn bị context Senior Beauty Architect..."})
        
        # KT1: Wave 1 — Pure Redis ops run in parallel (safe: no DB session contention)
        cur_settings, raw_draft = await asyncio.gather(
            self._get_currency_settings(),
            xohi_memory.get_order_draft(session_id),
        )
        order_draft = OrderDraft.model_validate(raw_draft) if raw_draft else None

        # Wave 2: DB ops — sequential to respect AsyncSession single-connection model
        hist_text = await self._fetch_chat_context(db, session_id)
        dna = await self._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)

        # Wave 3: Product context depends on cur_settings from Wave 1
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)

        # 1.0 Layer 1 Memory
        try:
            repo = SupportKnowledgeRepository(session=db)
            kb_service = SupportKnowledgeService(repo=repo)
            kb_index = await kb_service.get_knowledge_index(db)
        except Exception as e:
            logger.warning("[SupportAgent] KnowledgeIndex fetch failed: %s", e)
            kb_index = ""

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
        # C-1: Pass DB-authoritative price maps into pricing engine
        pb = await self._prepare_pricing_breakdown(db, request, dna, p_map=p_map, v_map=v_map)
        # KT1 Bugfix: cur_settings already fetched in Wave 1 — removed duplicate Redis call
        cart_text = self._render_cart_report(request, p_map, v_map, pb, ctx_text, cur_settings)
        
        # FOMO & Upsell
        from backend.database import current_tenant_id
        all_vouchers = (await db.execute(
            select(Voucher).where(
                Voucher.is_active == True,
                Voucher.deleted_at.is_(None),
                Voucher.tenant_id == (current_tenant_id.get() or "default")
            )
        )).scalars().all()
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
        except Exception as _ce:
            logger.warning("[SupportAgent] Integration config fetch failure: %s", _ce)

        # KT6: Token Budget Guard — trim context before LLM injection
        cart_text, ctx_text, hist_text, kb_index = self._trim_context_to_budget(
            cart_text, ctx_text, hist_text, kb_index
        )

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
        logger.info(f"🟢 [SupportAgent] final_reply (before Output Shield): {final_reply}")
        grounded_reply = _validate_grounding(final_reply, ctx)
        safe_reply = _sanitize_response(grounded_reply)
        logger.info(f"🟢 [SupportAgent] safe_reply (after Output Shield): {safe_reply}")
        
        if not safe_reply:
            logger.warning(f"[SupportAgent] Sanitized reply is empty for SID {session_id}! Triggering DB Fallback.")
            from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
            consultant = ConsultantHandler()
            safe_reply = consultant._generate_db_fallback(ctx)

        final_intent = ctx.intent or SupportIntent.UNKNOWN
        if ctx.ui_component == "PRODUCT_CARD" and p_info:
            if not ctx.ui_metadata: ctx.ui_metadata = {}
            ctx.ui_metadata.update({"type": "PRODUCT_CARD", "data": p_info.model_dump()})

        # 4. Persistence
        await self._save_history(db, session_id, request.message, safe_reply, final_intent, request.product_slug, dna.customer_name or request.customer_name, ctx.lead_data.customer_phone if ctx.lead_data else None)
        # Unified emit — _emit_inbox_update luôn sanitize qua _sanitize_for_notification()
        await self._emit_inbox_update(session_id, request.message)
        await db.flush()
        
        return SupportResponse(ok=True, reply=safe_reply, intent=final_intent, session_id=session_id, product_info=p_info, status="DONE", ui_metadata=ctx.ui_metadata, processed_order_id=ctx.processed_order_id)

    async def _prepare_pricing_breakdown(
        self, db: AsyncSession, request: SupportRequest, dna: NeuralDNA,
        p_map: Dict[str, ProductBase] | None = None,
        v_map: Dict[str, ProductVariant] | None = None,
    ) -> Dict[str, object]:
        """Unified Pricing Intelligence. C-1: ALL prices sourced from DB maps, never from client payload."""
        if request.pricing_context and request.pricing_context.subtotal > 0:
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
                if not p_id: continue
                # C-1 FIX: NEVER trust client-supplied price. Source from DB maps exclusively.
                p_db_item = _p_map.get(p_id)
                v_db_item = _v_map.get(str(v_raw.get("id", ""))) if v_raw.get("id") else None
                db_price = float(
                    v_db_item.price if v_db_item and v_db_item.price
                    else (p_db_item.price if p_db_item and p_db_item.price else 0)
                )
                if db_price <= 0:
                    logger.warning("[PricingBreakdown] C-1: DB price=0 for product_id=%s, skipping.", p_id)
                    continue
                p_name = p_db_item.name if p_db_item else str(p_raw.get("name", "SP"))
                input_items.append(PricingInputItem(
                    product_id=p_id, name=p_name,
                    quantity=int(it.get("quantity", 1) or 1),
                    unit_price=db_price
                ))

        if not input_items: return {"subtotal": 0.0, "final_payable": 0.0, "is_fallback": True}
        pb = PricingEngine.calculate(input_items, base_shipping_fee=30000.0)
        res = pb.model_dump()
        res["is_fallback"] = True
        return res

    async def _get_currency_settings(self) -> Dict[str, str]:
        """KT2: Redis Pipeline — 3 GETs batched into 1 round-trip."""
        try:
            async with xohi_memory.client.pipeline(transaction=False) as pipe:
                pipe.get("system:currency:symbol")
                pipe.get("system:currency:position")
                pipe.get("system:currency:thousand_sep")
                results = await pipe.execute()
            return {
                "symbol": results[0] or "₫",
                "position": results[1] or "suffix",
                "thousand_sep": results[2] or ".",
            }
        except Exception as e:
            logger.warning("[SupportAgent] Currency settings pipeline failed: %s", e)
            return {"symbol": "₫", "position": "suffix", "thousand_sep": "."}

    def _format_price(self, amount: float, settings: Dict[str, str]) -> str:
        formatted = f"{int(amount):,}".replace(",", settings["thousand_sep"])
        if settings["position"] == "prefix":
            return f"{settings['symbol']}{formatted}"
        return f"{formatted}{settings['symbol']}"

    @staticmethod
    def _trim_context_to_budget(
        cart_text: str, ctx_text: str, hist_text: str, kb_index: str,
        budget: int = 6000,
    ) -> tuple[str, str, str, str]:
        """KT6: Token Budget Guard — priority trim to keep prompt under budget.
        Trim order: hist_text → kb_index → ctx_text. cart_text is never trimmed (ground truth).
        """
        total = len(cart_text) + len(ctx_text) + len(hist_text) + len(kb_index)
        if total <= budget:
            return cart_text, ctx_text, hist_text, kb_index

        # Step 1: Trim hist to last 800 chars
        if len(hist_text) > 800:
            hist_text = hist_text[-800:]

        # Step 2: Trim kb_index if still over budget
        remaining = budget - len(cart_text) - len(ctx_text) - len(hist_text)
        if len(kb_index) > max(0, remaining):
            kb_index = kb_index[:max(0, remaining)] + "...[TRUNCATED]"

        # Step 3: Trim ctx_text (product description) if extreme overflow
        remaining = budget - len(cart_text) - len(hist_text) - len(kb_index)
        if len(ctx_text) > max(0, remaining):
            ctx_text = ctx_text[:max(0, remaining)] + "...[TRUNCATED]"

        logger.debug("[SupportAgent] KT6: Context trimmed from %d to budget %d chars.", total, budget)
        return cart_text, ctx_text, hist_text, kb_index

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
        if subtotal <= 0:
            if not all_vouchers:
                return ""
            fomo_text = "\n[CHƯƠNG TRÌNH ƯU ĐÃI & VOUCHER ĐANG DIỄN RA (Hãy chủ động giới thiệu cho khách)]:\n"
            for v in all_vouchers:
                if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
                    continue
                val_str = self._format_price(v.value, currency_settings) if v.type != "PERCENT" else f"{v.value}%"
                min_str = f" (Đơn từ {self._format_price(v.min_spend, currency_settings)})" if v.min_spend else " (Mọi đơn hàng)"
                title_str = f" - {v.title}" if v.title else ""
                fomo_text += f"- Mã {v.id}: Giảm {val_str}{min_str}{title_str}\n"
            return fomo_text + "--------------------------------\n"
        best_v, max_sav = None, 0.0
        for v in all_vouchers:
            if v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()):
                continue
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
        # Bugfix R01: Sort vouchers by min_spend ascending before finding the next tier
        valid_vouchers = [v for v in all_vouchers if not (v.id and (v.id.lower().startswith("check_") or v.id.lower().startswith("test_") or "test" in v.id.lower()))]
        next_v = next((v for v in sorted(valid_vouchers, key=lambda v: v.min_spend or 0) if (v.min_spend or 0) > subtotal), None)
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
        session_id = request.session_id or new_id()

        # ══ SECURITY GATE ① ── InputGuard (Elite V2.2) ════════════════════════
        # Must fire BEFORE any LLM call, DNA fetch, or enqueue to protect quota & RAM.
        from backend.services.commerce.security.input_guard import input_guard
        _is_safe, _guard_reason = await input_guard.validate_async(request.message)
        if not _is_safe:
            logger.warning("[SupportAgent] InputGuard rejected at entry. Reason: %s | SID: %s", _guard_reason, session_id)
            _rejection_reply = "Dạ Helen xin lỗi, em chỉ có thể hỗ trợ các thông tin sản phẩm và dịch vụ của osmo. Rất mong Anh/Chị thông cảm ạ! 🙏"
            return SupportResponse(ok=False, reply=_rejection_reply, intent=SupportIntent.UNKNOWN, session_id=session_id, status="REJECTED")
        # ══════════════════════════════════════════════════════════════════════

        dna = await self._fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
        c_name = dna.customer_name or request.customer_name or "Quý khách"
        if c_name in ["Khách ẩn danh", "Sếp"]: c_name = "Quý khách"
        msg_clean = request.message.strip().lower()

        # Mark session as unread in Redis Set (O(1) Memory & Latency compliance thưa sếp)
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.sadd("support:unread_sessions", session_id)
            except Exception as exc:
                logger.error(f"[SupportAgent] Failed to mark unread in Redis Set: {exc}")

        # ══════════════════════════════════════════════════════════════════════
        # OPTION 1: Chat trực tiếp trong box — tắt Helen, báo Admin Inbox
        # Keyword: [chat_inbox]
        # ══════════════════════════════════════════════════════════════════════
        if "[chat_inbox]" in msg_clean:
            # Set TAKEOVER: AI silenced — Human operator takes over
            await xohi_memory.client.set(f"support:takeover:{session_id}", "0", ex=86400 * 3)
            # Emit event to Admin Inbox so operator sees the session immediately
            await self._emit_inbox_update(session_id, request.message)
            reply_text = (
                "Dạ vâng ạ! Helen đã mời chuyên viên tư vấn trực tiếp vào cuộc trò chuyện này. "
                "Anh/Chị vui lòng chờ trong giây lát — chuyên viên sẽ phản hồi ngay tại đây ạ! 🤝\n\n"
                "*(Helen tạm dừng để nhường chỗ cho chuyên viên)*"
            )
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.ESCALATE, request.product_slug, c_name, request.customer_phone)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.ESCALATE, session_id=session_id, status="DONE")

        # ══════════════════════════════════════════════════════════════════════
        # OPTION 2: Chuyển qua Zalo OA — tắt Helen + thông báo Zalo + báo Inbox
        # Keyword: [zalo_oa]
        # ══════════════════════════════════════════════════════════════════════
        if "[zalo_oa]" in msg_clean or "tôi muốn kết nối trực tiếp với chuyên viên tư vấn" in msg_clean or "yêu cầu kết nối chuyên viên" in msg_clean or "gặp tư vấn viên" in msg_clean:
            from backend.services.core.zalo_service import zalo_service
            task = asyncio.create_task(
                zalo_service.push_support_notification(
                    customer_name=c_name,
                    message=request.message,
                    session_id=session_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            await xohi_memory.client.set(f"support:takeover:{session_id}", "0", ex=86400 * 3)
            await self._emit_inbox_update(session_id, request.message)

            reply_text = (
                "Dạ vâng ạ! Helen đã mở kết nối Zalo OA cho Anh/Chị và thông báo cho chuyên viên tư vấn. "
                "Chuyên viên sẽ theo dõi và có thể tiếp tục hỗ trợ ngay tại đây ạ! 💙\n\n"
                "*(Helen tạm dừng để nhường chỗ cho chuyên viên)*"
            )
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.ESCALATE, request.product_slug, c_name, request.customer_phone)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.ESCALATE, session_id=session_id, status="DONE")

        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0":
            from backend.services.core.zalo_service import zalo_service
            # Non-blocking background call to notify Sếp via Zalo OA (R03-compliant)
            task = asyncio.create_task(
                zalo_service.push_support_notification(
                    customer_name=c_name,
                    message=request.message,
                    session_id=session_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
            reply_text = offline_msg or "Dược sĩ tư vấn sẽ sớm phản hồi Quý khách qua Zalo OA. Vui lòng để lại lời nhắn ạ. 🌸"
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.UNKNOWN, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.UNKNOWN, session_id=session_id, status="DONE")
        
        takeover_val = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if takeover_val == "0":
            # AI is silenced! Human operator is handling this thưa sếp.
            # 1. Save customer's message to database history
            await self._save_history(db, session_id, request.message, None, SupportIntent.UNKNOWN, request.product_slug, c_name, request.customer_phone)
            # 2. Emit event so that Admin Inbox dashboard gets the new message instantly!
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            # 3. Return TAKEOVER status so frontend doesn't render any automatic assistant reply thưa sếp!
            return SupportResponse(ok=True, reply="", intent=SupportIntent.UNKNOWN, session_id=session_id, status="TAKEOVER")
        
        # Source settings & product info exactly once to avoid double database queries / calls (Performance optimization thưa sếp)
        cur_settings = await self._get_currency_settings()
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)

        is_system_prompt = request.message.strip().startswith("[system_")

        # ══ SYNCHRONOUS DB-FIRST FAST-PATH FOR QUICK BUTTONS (Elite V3.5 thưa sếp) ══
        db_first_reply = None
        db_first_intent = SupportIntent.PRODUCT_QUERY
        
        if p_info:
            msg_norm = request.message.lower().strip()
            p_name = p_info.name
            price_display = p_info.price_display or f"{int(p_info.price):,}đ".replace(",", ".")
            
            # Fetch product_metadata directly from DB using SQLAlchemy 2.0 to inject dynamic properties (Elite V2.2)
            from backend.database.models import ProductBase
            from sqlalchemy import select
            stmt = select(ProductBase.product_metadata).where(
                ProductBase.id == p_info.id,
                ProductBase.deleted_at.is_(None)
            )
            meta_res = await db.execute(stmt)
            product_meta = meta_res.scalar_one_or_none() or {}

            # Extract benefits & ingredients from product_metadata (Elite V2.6 Priority Chain)
            benefit_lines: list[str] = []
            section_label = "Công dụng nổi bật của sản phẩm:"
            if isinstance(product_meta, dict):
                # Priority 0: featured_ingredients — richest source (icon + name + benefit)
                fi_list = product_meta.get("featured_ingredients")
                if isinstance(fi_list, list) and fi_list:
                    for fi in fi_list:
                        fi_icon = fi.get("icon", "🧬")
                        fi_name = fi.get("name", "")
                        fi_benefit = fi.get("benefit", "")
                        if fi_name:
                            fi_name_safe = re.sub(r'<[^>]+>', ' ', str(fi_name))[:80].strip()
                            fi_benefit_safe = re.sub(r'<[^>]+>', ' ', str(fi_benefit))[:200].strip()
                            if fi_benefit_safe:
                                benefit_lines.append(f"{fi_icon} {fi_benefit_safe}")
                            else:
                                benefit_lines.append(f"{fi_icon} {fi_name_safe}")

                # Priority 1: key_ingredients (name + description)
                if not benefit_lines:
                    ki_list = product_meta.get("key_ingredients")
                    if isinstance(ki_list, list):
                        for ki in ki_list:
                            k_name = ki.get("name")
                            k_desc = ki.get("description")
                            if k_name:
                                k_name_safe = re.sub(r'<[^>]+>', ' ', str(k_name))[:80].strip()
                                k_desc_safe = re.sub(r'<[^>]+>', ' ', str(k_desc))[:200].strip() if k_desc else ""
                                if k_desc_safe:
                                    benefit_lines.append(f"🧬 {k_desc_safe}")
                                else:
                                    benefit_lines.append(f"🧬 {k_name_safe}")

                # Priority 2: raw ingredients string — label as "Thành phần" NOT "Lợi ích"
                if not benefit_lines:
                    ingredients_str = product_meta.get("ingredients")
                    if isinstance(ingredients_str, str) and ingredients_str.strip():
                        section_label = "Thành phần nổi bật:"
                        clean_ings = re.sub(r'<[^>]+>', ' ', ingredients_str).strip()
                        ings = [i.strip() for i in re.split(r'[,;]', clean_ings) if i.strip()]
                        for ing in ings[:4]:
                            benefit_lines.append(f"🧬 {ing}")

            # Priority 3: Fallback to parsing ctx_text lines under headers
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

            # Button 1: "Tư vấn" / `[system_consult]`
            if "[system_consult]" in msg_norm:
                benefit_text = "\n".join(benefit_lines[:4]) if benefit_lines else "🧬 Chiết xuất thảo dược tự nhiên chuẩn Nhật Bản."
                
                db_first_reply = (
                    f"Dạ Helen chào Anh/Chị! Rất vui được tư vấn liệu trình chăm sóc da hoàn hảo với {p_name} ạ! ✨\n\n"
                    f"🌸 {section_label}\n"
                    f"{benefit_text}\n\n"
                    f"💰 Giá ưu đãi độc quyền: {price_display}\n\n"
                    f"💬 Để nhận quà tặng độc quyền kèm đơn hàng hôm nay, Anh/Chị nhắn ngay Số Điện Thoại + Địa Chỉ để Helen lên đơn giao tận nơi nhé! 🌸"
                )
                db_first_intent = SupportIntent.PRODUCT_QUERY
            
            # Button 2: "An toàn da" / `[system_skin_barrier]` or "an toàn da"
            elif "[system_skin_barrier]" in msg_norm or "an toàn da" in msg_norm:
                # P0-3 Fix: Verify ingredients from product_metadata before claiming safety
                ingredients_raw = ""
                if isinstance(product_meta, dict):
                    ingredients_raw = str(product_meta.get("ingredients", "")).lower()
                
                safety_claims: list[str] = []
                # Only claim "no alcohol" if ingredients don't contain alcohol variants
                has_alcohol = any(kw in ingredients_raw for kw in ["alcohol", "ethanol", "cồn", "denat"])
                has_paraben = any(kw in ingredients_raw for kw in ["paraben", "methylparaben", "propylparaben"])
                has_fragrance = any(kw in ingredients_raw for kw in ["fragrance", "parfum", "hương liệu"])
                
                if not has_alcohol:
                    safety_claims.append("không chứa cồn")
                if not has_paraben:
                    safety_claims.append("không paraben")
                if not has_fragrance:
                    safety_claims.append("không hương liệu tổng hợp")
                
                if safety_claims:
                    safety_line = f"• {', '.join(safety_claims).capitalize()}.\n"
                else:
                    safety_line = "• Thành phần được kiểm nghiệm nghiêm ngặt theo tiêu chuẩn an toàn.\n"
                
                # Check legal certs from context
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
                db_first_intent = SupportIntent.PRODUCT_QUERY

            # Button 3: "Xuất xứ" / contains "xuất xứ" or "nguồn gốc"
            elif "xuất xứ" in msg_norm or "nguồn gốc" in msg_norm:
                origin_line = "Chính hãng nhập khẩu nguyên kiện."
                cert_line_origin = ""
                if ctx_text:
                    for line in ctx_text.split("\n"):
                        if "Xuất xứ:" in line:
                            origin_line = line.strip().replace("- ", "• ")
                        elif "Hồ sơ pháp lý:" in line:
                            cert_line_origin = "\n" + line.strip().replace("- ", "• ")
                
                # P1-5 Fix: Use dynamic origin from product_metadata instead of hardcoding "Nhật Bản"
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
                db_first_intent = SupportIntent.PRODUCT_QUERY

            # Button 4: "Công dụng" / contains "công dụng" or "thành phần"
            elif "công dụng" in msg_norm or "thành phần" in msg_norm:
                benefit_text_4 = "\n".join(benefit_lines[:6]) if benefit_lines else "🧬 Chứa các dưỡng chất tự nhiên cao cấp củng cố hàng rào bảo vệ da, giúp da căng bóng, mịn màng và trắng sáng khỏe mạnh."
                
                db_first_reply = (
                    f"Dạ gửi Anh/Chị thông tin chi tiết về thành phần & công dụng của {p_name} ạ! ✨\n\n"
                    f"{benefit_text_4}\n\n"
                    f"Anh/Chị nhắn lại tình trạng da hiện tại (da khô, dầu, mụn...) để Helen hướng dẫn cách sử dụng đạt hiệu quả tốt nhất nhé! 🌸"
                )
                db_first_intent = SupportIntent.PRODUCT_QUERY

        if db_first_reply:
            safe_reply = _sanitize_response(db_first_reply)
            await self._save_history(db, session_id, request.message, safe_reply, db_first_intent, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            logger.info(f"⚡ [DB-First Synchronous Gateway Bypass] Handled {request.message[:40]} in <20ms")
            return SupportResponse(ok=True, reply=safe_reply, intent=db_first_intent, session_id=session_id, product_info=p_info, status="DONE")
        # ══════════════════════════════════════════════════════════════════════

        # KT4: Greeting Trie Early-Exit — deterministic 0ms path, no LLM call needed
        if not is_system_prompt and not request.cart_items and _is_definite_greeting(request.message):
            _c = c_name if c_name not in ["Quý khách"] else ""
            _salutation = f" {_c}" if _c else ""
            greeting_reply = (
                f"Xin chào{_salutation}! 🌸 Helen rất vui được hỗ trợ Anh/Chị. "
                "Anh/Chị cần tư vấn về sản phẩm, đơn hàng hay bất kỳ điều gì, "
                "cứ nhắn Helen nhé! ✨"
            )
            await self._save_history(db, session_id, request.message, greeting_reply, SupportIntent.GENERAL_ADVICE, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return SupportResponse(ok=True, reply=greeting_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")

        if not is_system_prompt:
            try:
                masked_msg = await self._mask_sensitive_medical_terms(request.message)
                fast_res = await asyncio.wait_for(trinity_bridge.run(_fast_intent_agent, masked_msg, deps=FastIntentDeps(customer_name=c_name, product_name=p_info.name if p_info else None), role=trinity_bridge.ROLE_FAST, timeout=12.0, per_model_timeout=5.0), timeout=13.0)
                f_data = cast(FastIntentResponse, fast_res)
                if f_data.intent == "GREETING" and f_data.quick_reply and not request.cart_items:
                    await self._save_history(db, session_id, request.message, f_data.quick_reply, SupportIntent.GENERAL_ADVICE, request.product_slug, c_name, request.customer_phone)
                    await db.flush()
                    return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
            except Exception: pass

        heuristic_res = await self._try_heuristic_sync(request, db, session_id, p_info, c_name)
        if heuristic_res: return heuristic_res

        # ══ SYNC ORDER FAST-PATH (Elite V7.0) ═════════════════════════════════
        # Detect clear purchase intent synchronously — avoids enqueue + LLM round-trip (~60s → <1s)
        order_fp = await self._try_sync_order_fast_path(request, db, session_id, p_info, c_name)
        if order_fp: return order_fp

        # ══ SYNC SLOT-FILL FAST-PATH (Elite V7.0) ═════════════════════════════
        # When draft exists and user provides phone+address, fill slots & create order synchronously
        slot_fp = await self._try_sync_slot_fill(request, db, session_id, p_info, c_name)
        if slot_fp: return slot_fp
        # ══════════════════════════════════════════════════════════════════════

        # Elite V2.2: Removed early system prefix stripping here. We must keep `[system_consult]` 
        # so that OrderHandler can detect and bypass it correctly in the worker.
        enqueue_data = request.model_dump()
        enqueue_data["message"] = request.message

        if xohi_memory._use_redis and xohi_memory.client: await xohi_memory.client.delete(f"pulse:{session_id}:cache")
        task_id = await self.enqueue_chat(request_data=enqueue_data, session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

    async def _try_heuristic_sync(self, request: SupportRequest, db: AsyncSession, session_id: str, p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None) -> Optional[SupportResponse]:
        msg_norm = request.message.lower().strip()
        # Elite V2.2: Disable sync heuristics for Origin/Legal/Trust queries to force AI Reasoning & FOMO
        if any(kw in msg_norm for kw in ["thành phần", "chiết xuất", "ship", "phí", "nguồn gốc", "xuất xứ", "chính hãng", "uy tín", "giấy phép", "pháp lý"]): return None
        cur_settings = await self._get_currency_settings()
        if any(kw in msg_norm for kw in ["giá", "bao nhiêu"]) and p_info and not request.cart_items:
            final_reply = f"Dạ liệu trình **{p_info.name}** giá từ **{p_info.price_display}** ạ. 🌸"
            await self._save_history(db, session_id, request.message, final_reply, SupportIntent.PRICE_QUERY, request.product_slug, customer_name)
            await self._emit_inbox_update(session_id, request.message)
            return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.PRICE_QUERY, session_id=session_id, status="DONE")
        
        is_address = any(kw in msg_norm for kw in ["địa chỉ", "ở đâu"])
        is_hotline = any(kw in msg_norm for kw in ["điện thoại", "hotline"])
        if is_address or is_hotline:
            raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
            if not raw_cfg: return None
            ci = json.loads(raw_cfg).get("contact_info", {})
            final_reply = f"Dạ địa chỉ: **{ci.get('address')}** ạ. 🌸" if is_address else f"Hotline: **{ci.get('hotline')}** ạ. 🌸"
            await self._save_history(db, session_id, request.message, final_reply, SupportIntent.POLICY_QUERY, request.product_slug, customer_name)
            await self._emit_inbox_update(session_id, request.message)
            return SupportResponse(ok=True, reply=final_reply, intent=SupportIntent.POLICY_QUERY, session_id=session_id, status="DONE")
        return None

    # ══════════════════════════════════════════════════════════════════════
    # SYNC ORDER FAST-PATH (Elite V7.0) — Zero-LLM Order Initiation
    # Catches patterns like "cho tôi 3 hộp", "lấy 2 lọ", "mua 1 set"
    # and responds instantly (<1s) instead of enqueuing to worker (~60s)
    # ══════════════════════════════════════════════════════════════════════
    async def _try_sync_order_fast_path(
        self, request: SupportRequest, db: AsyncSession, session_id: str,
        p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None
    ) -> Optional[SupportResponse]:
        if not p_info:
            return None  # Cannot create draft without knowing which product

        msg = request.message.lower().strip()
        # Skip if message looks like a system command or question
        if msg.startswith("[system_") or "?" in msg:
            return None

        # Pattern: buying keyword + optional quantity + unit keyword
        # Matches: "cho tôi 3 hộp", "lấy 2 lọ", "mua 1 set", "cho mình hộp", "đặt 5 chai"
        import unicodedata
        msg_nfkc = unicodedata.normalize("NFKC", msg)
        buy_kws = ["cho", "mua", "đặt", "lấy", "gửi", "ship"]
        unit_kws = ["hộp", "lọ", "chai", "cái", "bộ", "set", "tuýp", "gói", "túi", "sp", "sản phẩm"]

        has_buy = any(kw in msg_nfkc for kw in buy_kws)
        has_unit = any(kw in msg_nfkc for kw in unit_kws)
        # Only intercept short, clear purchase messages (< 40 chars to avoid complex queries)
        if not (has_buy and has_unit and len(msg) < 40):
            return None

        # Extract quantity (default 1 if not specified)
        qty_match = re.search(r"(\d+)", msg_nfkc)
        quantity = int(qty_match.group(1)) if qty_match else 1
        if quantity < 1 or quantity > 100:
            return None  # Unreasonable quantity, let normal flow handle

        logger.info(f"⚡ [SyncOrderFastPath] Detected purchase: '{msg}' → {p_info.name} x{quantity}")

        # Build draft items from the product the customer is viewing
        unit_price = float(p_info.price or 0)
        if unit_price <= 0:
            return None  # Cannot create order without price

        draft_item = {
            "product_id": p_info.id,
            "id": p_info.slug,
            "name": p_info.name,
            "price": unit_price,
            "quantity": quantity,
        }

        # Create or update OrderDraft in Redis
        draft = OrderDraft(
            session_id=session_id,
            items=[draft_item],
            customer_name=customer_name if customer_name != "Quý khách" else None,
            is_definite_intent=True,
        )
        await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))

        # Build personalized response
        c_display = customer_name if customer_name and customer_name != "Quý khách" else "mình"
        total_price = unit_price * quantity
        formatted_total = "{:,.0f}".format(total_price).replace(",", ".")
        p_name_short = p_info.name.split(" - ")[0] if " - " in p_info.name else p_info.name
        if len(p_name_short) > 50:
            p_name_short = p_name_short[:50] + "..."

        debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""
        reply = (
            f"{debug_prefix}Dạ Helen nhận đơn **{quantity} {p_name_short}** "
            f"({formatted_total}đ) cho {c_display} rồi ạ! 🌸\n"
            f"{c_display.capitalize()} cho em xin nhanh:\n"
            f"📞 **Số điện thoại**\n"
            f"📍 **Địa chỉ nhận hàng**\n"
            f"để em lên bill giao tận nơi luôn nhé! ✨"
        )

        safe_reply = _sanitize_response(reply)
        await self._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
        await self._emit_inbox_update(session_id, request.message)
        await db.flush()
        logger.info(f"⚡ [SyncOrderFastPath] Responded in <1s for '{msg}' — draft created")
        return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, product_info=p_info, status="DONE")

    # ══════════════════════════════════════════════════════════════════════
    # SYNC SLOT-FILL FAST-PATH (Elite V7.0) — Zero-LLM Order Completion
    # When draft exists, detect phone + address and create order instantly
    # ══════════════════════════════════════════════════════════════════════
    async def _try_sync_slot_fill(
        self, request: SupportRequest, db: AsyncSession, session_id: str,
        p_info: Optional[SupportProductInfo] = None, customer_name: Optional[str] = None
    ) -> Optional[SupportResponse]:
        # 1. Check for active draft in Redis
        raw_draft = await xohi_memory.get_order_draft(session_id)
        if not raw_draft:
            return None

        try:
            draft = OrderDraft.model_validate(raw_draft)
        except Exception:
            return None

        if not draft.items:
            return None  # Draft has no items, cannot complete

        msg = request.message.strip()
        msg_lower = msg.lower()

        # Skip system commands
        if msg_lower.startswith("[system_"):
            return None

        # 2. Deterministic phone extraction
        digits_only = re.sub(r"\D", "", msg)
        phone_match = re.search(r"0\d{9}", digits_only)
        extracted_phone = phone_match.group() if phone_match else None

        # 3. Deterministic address extraction
        has_addr_signal = "/" in msg or any(
            kw in msg_lower for kw in [
                "đường", "phố", "phường", "quận", "huyện", "xã", "tỉnh",
                "tp", "thành phố", "số", "ngõ", "ngách", "p.", "q."
            ]
        )
        # Address: message has address signals OR is long enough with digits (not just a phone)
        digit_ratio = len(digits_only) / len(msg) if msg else 0
        extracted_address = None
        if has_addr_signal or (len(msg) > 15 and digit_ratio < 0.5):
            # Remove phone number from message to get address portion
            addr_text = msg
            if extracted_phone and extracted_phone in digits_only:
                # Remove the phone number portion, keeping the rest as address
                addr_text = re.sub(r"0\d{9}", "", msg).strip().strip(",").strip()
            if len(addr_text) > 5:  # Must have some address text remaining
                extracted_address = addr_text

        # 4. Fill slots into draft
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
        # Also fill phone into existing draft that already has address but missing phone
        if extracted_phone and not draft.customer_phone and draft.customer_address:
            from backend.services.commerce.logic.lead_extractor import validate_vietnam_phone
            validated = validate_vietnam_phone(extracted_phone)
            if validated:
                draft.customer_phone = validated
                filled_something = True

        if not filled_something:
            return None  # Nothing to fill, let normal flow handle

        # 5. Persist updated draft
        await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))

        debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""
        c_display = customer_name if customer_name and customer_name != "Quý khách" else "mình"

        # 6. Check if draft is now complete → create order
        if draft.is_complete:
            # Resolve address for shipping days
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
                    # Ambiguous address — ask for clarification
                    provinces = ", ".join(geo.possible_provinces)
                    await xohi_memory.set_order_draft(session_id, draft.model_dump(mode='json'))
                    reply = f"{debug_prefix}Dạ địa chỉ của {c_display} trùng tên ở nhiều nơi ({provinces}), {c_display} cho Helen xin thêm Tỉnh/Thành phố nhé! 🌸"
                    safe_reply = _sanitize_response(reply)
                    await self._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
                    await self._emit_inbox_update(session_id, request.message)
                    await db.flush()
                    return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")
            except Exception as geo_err:
                logger.warning(f"[SyncSlotFill] Geo resolution failed: {geo_err}")

            # Create order via OrderService
            try:
                from backend.services.commerce.order import OrderService
                from backend.schemas.order import OrderCreateRequest
                from backend.services.commerce.logic.lead_extractor import lead_extractor
                from backend.database import current_tenant_id

                # Resolve user identity
                from backend.services.commerce.user_service import user_service
                tid = current_tenant_id.get() or "default"
                resolved_user = None
                if draft.customer_phone:
                    resolved_user, _, _, _ = await user_service.get_or_resolve_customer(
                        db=db, phone=draft.customer_phone,
                        name=draft.customer_name or customer_name, 
                        current_address=draft.customer_address, tenant_id=tid
                    )

                user_id = str(resolved_user.id) if resolved_user else "guest"

                # Apply combo deals to items
                enriched_items = []
                for it in draft.items:
                    enriched_item = dict(it)
                    # Ensure required fields exist
                    enriched_item.setdefault("id", enriched_item.get("product_id", ""))
                    enriched_item.setdefault("product_id", enriched_item.get("id", ""))
                    enriched_item.setdefault("quantity", enriched_item.get("qty", 1))
                    enriched_item.setdefault("unit_price", enriched_item.get("price", 0))
                    enriched_items.append(enriched_item)

                # Check for combo deals
                combo_items = await PromotionService.apply_combo_deals(db, enriched_items)
                if combo_items:
                    enriched_items = combo_items

                total = sum(float(it.get("price") or it.get("unit_price") or 0) * int(it.get("quantity") or it.get("qty") or 1) for it in enriched_items)

                order_data = OrderCreateRequest(
                    items=enriched_items,
                    total_amount=total,
                    customer_name=draft.customer_name or customer_name or "Quý khách",
                    customer_email=f"{draft.customer_phone}@helen.osmo.vn",
                    customer_phone=draft.customer_phone,
                    customer_address=draft.customer_address,
                )

                result = await OrderService.create_order(db, order_data, ip="0.0.0.0", ua="Helen-SyncFastPath", user_id=user_id)
                order_id = result.id
                await xohi_memory.clear_order_draft(session_id)

                # Build professional confirmation
                formatted_total = "{:,.0f}".format(total).replace(",", ".")
                item_parts = []
                for it in enriched_items:
                    name = str(it.get("name", "SP"))
                    qty = int(it.get("quantity") or it.get("qty") or 1)
                    part = f"📦 {name} (x{qty})"
                    gifts = it.get("gifts") or []
                    if gifts:
                        gift_strs = [f"{g.get('name', 'SP')} (x{g.get('qty', 1)})" for g in gifts if isinstance(g, dict)]
                        if gift_strs:
                            part += f"\n   🎁 + {', '.join(gift_strs)}"
                    item_parts.append(part)
                items_text = "\n".join(item_parts)

                reply = (
                    f"{debug_prefix}Dạ Helen chúc mừng {c_display} đặt hàng thành công! 🌸\n\n"
                    f"📋 **CHI TIẾT ĐƠN HÀNG**\n"
                    f"🆔 Mã đơn: **{order_id[-8:].upper()}**\n"
                    f"{items_text}\n"
                    f"💰 Tổng: **{formatted_total}đ**\n"
                    f"🚚 Dự kiến: **{shipping_days}**\n\n"
                    f"{c_display.capitalize()} nhớ để ý điện thoại khi shipper gọi nha! 📞\n"
                    f"Cảm ơn {c_display} đã tin tưởng osmo! 💖"
                )

                safe_reply = _sanitize_response(reply)
                await self._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
                await self._emit_inbox_update(session_id, request.message)
                await db.flush()
                logger.info(f"⚡ [SyncSlotFill] Order created: {order_id} — full sync path")
                return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")

            except Exception as order_err:
                logger.error(f"[SyncSlotFill] Order creation failed: {order_err}")
                # Fall through to enqueue
                return None

        # 7. Draft incomplete — acknowledge what we received, ask for what's missing
        missing = draft.missing_slots
        # Build item summary for context
        item_names = ", ".join([
            f"{it.get('name', 'SP')} x{it.get('quantity', 1)}"
            for it in draft.items
        ])

        if "Số điện thoại" in missing and "Địa chỉ cụ thể" in missing:
            # Acknowledged address or phone from this turn
            reply = (
                f"{debug_prefix}Dạ Helen đã nhận đơn **{item_names}** cho {c_display} rồi ạ! 🌸\n"
                f"{c_display.capitalize()} cho em xin nhanh:\n"
                f"📞 **Số điện thoại**\n"
                f"📍 **Địa chỉ nhận hàng**\n"
                f"để em lên bill giao tận nơi luôn nhé! ✨"
            )
        elif "Số điện thoại" in missing:
            ack = f"Dạ Helen đã ghi nhận địa chỉ của {c_display} rồi ạ."
            reply = f"{debug_prefix}{ack} {c_display.capitalize()} cho em xin thêm **Số Điện Thoại** để shipper liên lạc nha! 🌸"
        elif "Địa chỉ cụ thể" in missing:
            ack = f"Dạ Helen đã lưu SĐT **{draft.customer_phone}** của {c_display} rồi ạ."
            reply = f"{debug_prefix}{ack} {c_display.capitalize()} cho em xin thêm **Địa chỉ cụ thể** để gửi hàng về tận cửa luôn nhé! 🌸"
        else:
            return None  # Should not happen — draft.is_complete would be True

        safe_reply = _sanitize_response(reply)
        await self._save_history(db, session_id, request.message, safe_reply, SupportIntent.PURCHASE, request.product_slug, customer_name, request.customer_phone)
        await self._emit_inbox_update(session_id, request.message)
        await db.flush()
        logger.info(f"⚡ [SyncSlotFill] Slot filled — missing: {missing}")
        return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")

support_agent = SupportAgentOperative()
