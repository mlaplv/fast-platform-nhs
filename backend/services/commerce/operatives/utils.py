"""
Support Agent Utilities — SUPPORT_NAME_CLIENT (Architect's Edition)
==================================================================
Elite V5.5: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations

import json
import logging
import os
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "mock_key_for_import_compliance"
import re
from typing import Optional, Dict, Type, List, Tuple
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase
from backend.schemas.support import SupportProductInfo
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.services.xohi_memory import xohi_memory
from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext

logger = logging.getLogger("arq.worker")

# ══════════════════════════════════════════════════════════════
# GREETING TRIE (0ms, no LLM)
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
        normalized == kw or normalized.startswith(kw + " ")
        for kw in _GREETING_TRIE
    )

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI MODELS & AGENTS
# ══════════════════════════════════════════════════════════════
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

_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    "gemini-2.5-flash",  # explicitly specify default engine matching stack
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
    "gemini-2.5-flash",
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

# ══════════════════════════════════════════════════════════════
# PRODUCT CONTEXT RESOLVER
# ══════════════════════════════════════════════════════════════
async def _fetch_product_context(db: AsyncSession, slug: Optional[str], currency_settings: Dict[str, str]) -> Tuple[str, Optional[SupportProductInfo]]:
    """Fetch product info via SQLAlchemy 2.0 Scalar projection."""
    if not slug:
        return "", None
        
    if any(p in slug for p in ["chinh-sach", "gioi-thieu", "tuyen-dung", "dieu-khoan", "thanh-toan", "kiem-hang", "bao-hanh"]):
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
        if not p_row:
            return "", None
            
        img_url = p_row.images[0] if p_row.images and len(p_row.images) > 0 else None
        
        def fmt(amt: float) -> str:
            formatted = f"{int(amt):,}".replace(",", currency_settings.get("thousand_sep", "."))
            if currency_settings.get("position") == "prefix":
                return f"{currency_settings.get('symbol', 'đ')}{formatted}"
            return f"{formatted}{currency_settings.get('symbol', 'đ')}"

        _name_safe = re.sub(r'<[^>]+>', ' ', str(p_row.name or ''))[:100].strip()
        _desc_safe = re.sub(r'<[^>]+>', ' ', str(p_row.short_description or ''))[:300].strip()

        p_info = SupportProductInfo(
            id=str(p_row.id),
            name=_name_safe,
            price=float(p_row.price or 0),
            price_display=fmt(float(p_row.discount_price or p_row.price or 0)),
            slug=p_row.slug or "",
            image_url=img_url,
            stock=p_row.stock
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {_name_safe}\nMô tả: {_desc_safe}\nGiá niêm yết: {p_row.price} VND\n"
        if p_row.discount_price:
            ctx += f"Giá khuyến mãi: {p_row.discount_price} VND\n"
        ctx += f"Tồn kho thực tế: {p_row.stock or 0} sản phẩm\n"

        ctx += "\n[THÀNH PHẦN NỔI BẬT & CÔNG DỤNG]:\n"

        if p_row.product_metadata:
            meta = p_row.product_metadata
            fi_list = meta.get("featured_ingredients")
            if isinstance(fi_list, list) and fi_list:
                for fi in fi_list:
                    if isinstance(fi, dict):
                        fi_name = fi.get("name", "")
                        fi_benefit = fi.get("benefit", "")
                        if fi_name:
                            fi_name_safe = re.sub(r'<[^>]+>', ' ', str(fi_name))[:80].strip()
                            fi_benefit_safe = re.sub(r'<[^>]+>', ' ', str(fi_benefit))[:200].strip()
                            ctx += f"- {fi_name_safe}: {fi_benefit_safe}\n"
            elif "key_ingredients" in meta and isinstance(meta["key_ingredients"], list):
                for ki in meta["key_ingredients"]:
                    if isinstance(ki, dict):
                        k_name = ki.get("name", "")
                        k_desc = ki.get("description", "")
                        if k_name:
                            k_name_safe = re.sub(r'<[^>]+>', ' ', str(k_name))[:80].strip()
                            k_desc_safe = re.sub(r'<[^>]+>', ' ', str(k_desc))[:200].strip()
                            ctx += f"- {k_name_safe}: {k_desc_safe}\n"

            if "ingredients" in meta and isinstance(meta["ingredients"], str):
                _ing_safe = re.sub(r'<[^>]+>', ' ', str(meta['ingredients']))[:500].strip()
                ctx += f"\n[BẢNG THÀNH PHẦN CHI TIẾT]:\n{_ing_safe}\n"
                
            if "knowledge_graph" in meta and isinstance(meta["knowledge_graph"], dict):
                kg = meta["knowledge_graph"]
                ctx += f"\n[KNOWLEDGE GRAPH - SƠ ĐỒ TRI THỨC Y KHOA]:\n"
                if kg.get("main_takeaway"):
                    ctx += f"- KẾT LUẬN LÂM SÀNG: {kg['main_takeaway']}\n"
                if kg.get("expert_claim"):
                    ctx += f"- KHẲNG ĐỊNH CHUYÊN MÔN: {kg['expert_claim']}\n"
                if kg.get("entities") and isinstance(kg["entities"], list):
                    ctx += "- THỰC THỂ (ENTITIES):\n"
                    for ent in kg["entities"][:5]:
                        if isinstance(ent, dict):
                            e_name = re.sub(r'<[^>]+>', '', str(ent.get("name", "")))
                            e_type = re.sub(r'<[^>]+>', '', str(ent.get("type", "")))
                            e_desc = re.sub(r'<[^>]+>', '', str(ent.get("description", "")))
                            ctx += f"  + [{e_type}] {e_name}: {e_desc}\n"
                
        meta_dict: Dict[str, object] = p_row.product_metadata or {}
        origin: str = str(meta_dict.get("origin", "Chưa cập nhật"))
        
        real_certs: List[str] = []
        if meta_dict.get("notification_no"):
            auth = str(meta_dict.get("authority", "Cơ quan quản lý"))
            real_certs.append(f"Số phiếu công bố {str(meta_dict['notification_no'])} ({auth})")
        
        if meta_dict.get("certificates"):
            certs = meta_dict.get("certificates")
            if isinstance(certs, list): 
                real_certs.extend([str(c) for c in certs])
            elif isinstance(certs, str): 
                real_certs.append(certs)
            
        certs_str: str = ", ".join(real_certs) if real_certs else "Chưa có chứng nhận"
        
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

# ══════════════════════════════════════════════════════════════
# OUTPUT SHIELD & SANITIZATION
# ══════════════════════════════════════════════════════════════
_SYSTEM_LEAK_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"(BẢN SẮC|PHONG THÁI|SÁT THỦ BÁN HÀNG|NHIỆM VỤ TỐI THƯỢNG|QUY TẮC VÀNG|ELITE PROTOCOL)", re.IGNORECASE),
    re.compile(r"(KIẾN TRÚC SƯ SẮC ĐẸP|NHẠY BÉN DỮ LIỆU|TRẠI NGHIỆM THƯỢNG LƯU|KỶ LUẬT THÀNH PHẦN)", re.IGNORECASE),
    re.compile(r"(KÍCH HOẠT FOMO|CHỈ THỊ FOMO|CHỈ THỊ GROUND TRUTH)", re.IGNORECASE),
    re.compile(r"(SYSTEM PROMPT|bạn là helen.{0,40}senior beauty architect)", re.IGNORECASE),
    re.compile(r"(TỔNG THANH TOÁN CUỐI CÙNG.{0,30}PHÁP LỆNH)", re.IGNORECASE),
    re.compile(r"(system_prompt|dynamic_prompt|ConsultantDeps|trinity_bridge|SupportRouter|GuardrailHandler|RunContext)", re.IGNORECASE),
    re.compile(r"Nano-penetration", re.IGNORECASE),
]
_SAFE_FALLBACK_REPLY = "Dạ Helen rất xin lỗi, em vừa gặp sự cố nhỏ trong xử lý. Anh/Chị thông cảm thử lại sau nhé! 🌸"

_NOTIFY_LABEL_MAP: Dict[str, str] = {
    "[system_consult]": "Tư vấn sản phẩm",
    "[system_skin_barrier]": "Kiểm tra độ phù hợp da",
    "[system_checkin]": "Thực hiện điểm danh",
    "[system_follow_up_trigger]": "(Nhắc nhở chăm sóc tự động)",
    "[chat_inbox]": "Yêu cầu kết nối tư vấn trực tiếp",
}

def _sanitize_for_notification(raw_msg: str) -> str:
    """Chuẩn hóa tin nhắn khách hàng để hiển thị an toàn trong Notification Hub."""
    if not raw_msg or not raw_msg.strip():
        return "Tin nhắn mới"
    msg = raw_msg.strip()
    msg_lower = msg.lower()
    for token, label in _NOTIFY_LABEL_MAP.items():
        if token in msg_lower:
            return label
    _leak_keywords = [
        "vui lòng đóng vai", "bạn là helen", "system prompt",
        "chỉ thị:", "prompt:", "khung hướng dẫn:", "[system_"
    ]
    if any(k in msg_lower for k in _leak_keywords):
        return "Yêu cầu tư vấn"
    if len(msg) > 200 and any(k in msg_lower for k in ["skin_profile", "loại da", "chăm sóc da", "phân tích"]):
        return "Gửi hồ sơ phân tích da và yêu cầu tư vấn"
    if len(msg) > 120:
        msg = msg[:117] + "..."
    return msg

def _validate_grounding(reply: str, ctx: SupportContext) -> str:
    """Anti-Hallucination & Anti-Delusion Grounding Shield."""
    if not reply or "[fallback]" in reply:
        return reply

    delusion_patterns = [
        (r"(đã\s+hoàn\s+tiền|đã\s+refund|hoàn\s+lại\s+tiền\s+cho)", "Helen đã ghi nhận yêu cầu hoàn tiền và gửi bộ phận CSKH xử lý lập tức cho"),
        (r"(đã\s+hủy\s+đơn\s+hàng\s+trên\s+hệ\s+thống|đơn\s+hàng\s+của\s+chị\s+đã\s+hủy|đã\s+hủy\s+đơn)", "Helen đã ghi nhận yêu cầu hủy đơn hàng và chuyển trạng thái xử lý cho"),
        (r"(đã\s+gửi\s+hàng\s+đi|đơn\s+hàng\s+đang\s+được\s+giao|đã\s+xuất\s+kho|đang\s+giao\s+hỏa\s+tốc)", "Helen đã ghi nhận yêu cầu lên đơn hàng để chuẩn bị giao cho"),
        (r"(đã\s+thanh\s+toán\s+thành\s+công|thanh\s+toán\s+hoàn\s+tất)", "Helen đã ghi nhận thông tin xác nhận thanh toán của")
    ]
    for pattern, replacement in delusion_patterns:
        reply = re.sub(pattern, replacement, reply, flags=re.IGNORECASE)

    if ctx.p_info:
        price_matches = list(re.finditer(r"\b(\d{1,3}(?:\.\d{3})+|\d{4,8})\s*(?:đ|đồng|vnd|vnđ|k)\b", reply, re.IGNORECASE))
        for m in price_matches:
            full_match = m.group(0)
            clean_mention = m.group(1).replace(".", "")
            try:
                mention_val = float(clean_mention)
                real_price = ctx.p_info.price
                discount_price = ctx.p_info.price_display
                
                if mention_val > 1000:
                    is_real_match = abs(mention_val - real_price) < 100
                    is_discount_match = False
                    dp_num = ""
                    if discount_price:
                        dp_num = "".join(c for c in discount_price if c.isdigit())
                        if dp_num:
                            is_discount_match = abs(mention_val - float(dp_num)) < 100
                    
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
                        correct_price = discount_price or f"{int(real_price):,}đ".replace(",", ".")
                        reply = reply.replace(full_match, correct_price)
                        logger.warning(f"🛡️ [Anti-Hallucination] Corrected hallucinated price: {full_match} -> {correct_price}")
            except Exception:
                pass

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

    potential_codes: List[str] = []
    for code in potential_codes_raw:
        code_upper = code.upper()
        if code.isdigit() or code_upper in EXCLUDED_ABBREVIATIONS:
            continue
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
                reply = re.sub(rf"(?:mã|code|voucher)\s*[\"'\u2018\u2019]?\s*{re.escape(code)}\s*[\"'\u2018\u2019]?", "", reply, flags=re.IGNORECASE)
                reply = reply.replace(code, "")
                reply = re.sub(r" {2,}", " ", reply)
                reply = re.sub(r"\s+([,\.!?])", r"\1", reply)
                logger.warning(f"🛡️ [Anti-Hallucination] Removed hallucinated voucher: {code}")

    return reply

def _sanitize_response(text: str) -> str:
    """Surgical leak prevention."""
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    clean = re.sub(r"/[a-zA-Z_]\w*(/[a-zA-Z_]\w*)+(\.\w+)?", "[REDACTED_PATH]", clean)
    clean = re.sub(r"(0|84|(\+84))(\d{2,3})[\s\.\-]?(\d{3})[\s\.\-]?(\d{3,4})", r"\1\3****\5", clean)
    for _p in _SYSTEM_LEAK_PATTERNS:
        if _p.search(clean):
            logger.warning("[OutputShield] System prompt leakage detected. Fallback triggered.")
            return _SAFE_FALLBACK_REPLY
    clean = re.sub(r"[Nn]hau\s+[Tt]hai", "Placenta", clean)
    clean = re.sub(r"\*{3,}", "**", clean)
    return clean.strip()
