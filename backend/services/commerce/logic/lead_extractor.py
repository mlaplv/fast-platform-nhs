"""
Lead Extractor Service — Elite V2.2 (Architect's Edition)
========================================================
Refined for 100% static typing, Martial Combo Protocol, and zero-leak logic.
"""
from __future__ import annotations
import asyncio
import logging
import re
from typing import List, Optional, Dict, Union, TypedDict, Tuple
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.order import order_service
from backend.services.commerce.logic.location_resolver import location_resolver, ResolvedLocation
from backend.services.user_service import user_service
from backend.schemas.order import OrderCreateRequest
from backend.database.models import ProductBase

logger = logging.getLogger("api-gateway")

class LeadOrderItemDict(TypedDict):
    """Elite V2.2: Precise Type Definition for Internal Order Items."""
    product_id: str
    name: str
    quantity: int
    price: float

class LeadOrderItem(BaseModel):
    model_config = ConfigDict(strict=True) # Elite R0.2: Force strict typing
    name: str = Field(..., description="Tên sản phẩm")
    quantity: int = Field(1, description="Số lượng")
    price: Optional[float] = Field(0.0, description="Giá sản phẩm nếu có")
    id: Optional[str] = Field(None, description="Mã định danh sản phẩm (slug/uuid)")

class ExtractedLead(BaseModel):
    model_config = ConfigDict(strict=False)
    customer_name: Optional[str] = Field(None, description="Tên khách hàng nếu có")
    customer_phone: Optional[str] = Field(None, description="Số điện thoại Việt Nam (10 số)")
    customer_address: Optional[str] = Field(None, description="Địa chỉ giao hàng chi tiết")
    items: List[LeadOrderItem] = Field(default_factory=list, description="Danh sách sản phẩm trích xuất được")
    is_definite_purchase: bool = Field(False, description="True nếu khách hàng đã xác nhận chốt đơn hoặc đồng ý mua")
    is_new_customer: bool = Field(False, description="True nếu đây là khách hàng mới")
    address_status: str = Field("SAME", description="SAME, CHANGED, or NEW")
    previous_address: Optional[str] = Field(None, description="Địa chỉ cũ của khách nếu có")
    processed_order_id: Optional[str] = Field(None, description="ID đơn hàng đã tạo (nếu có)")
    needs_price_quote: bool = Field(False, description="True nếu số lượng quá lớn (>5) cần báo giá riêng")
    shipping_days: Optional[str] = Field(None, description="Thời gian giao hàng dự kiến")
    possible_provinces: List[str] = Field(default_factory=list, description="Danh sách tỉnh thành khả nghi nếu địa chỉ mơ hồ")


_lead_extraction_agent = Agent(
    output_type=ExtractedLead,
    system_prompt=(
        "Bạn là một chuyên gia trích xuất đơn hàng tại Việt Nam (Elite Specialist).\n"
        " QUY TẮC CHIẾN THUẬT:\n"
        " 1. TRÍCH XUẤT CHÍNH XÁC: SĐT (10 số), Địa chỉ, Sản phẩm, Tên khách.\n"
        " 2. ĐỊNH DẠNG STAFF: 'Cho 1 đơn về : [Địa chỉ], [SĐT], [Tên]' -> Parse địa chỉ, SĐT, tên. Nếu không có 'lọ/combo' đi kèm, đặt items rỗng để hệ thống hỏi lại.\n"
        " 3. ĐỊNH DẠNG ĐỊNH LƯỢNG: 'Lấy 2 lọ', 'Cho 3 combo', 'Gửi 5 hộp' -> Phải trích xuất chính xác số lượng vào items.\n"
        " 4. NHẬN DIỆN XÁC NHẬN: 'Ok', 'Chốt', 'Đồng ý', 'Gửi đi' -> is_definite_purchase = true.\n"
        " 5. Tuyệt đối không bịa thông tin."
    )
)

def validate_vietnam_phone(phone: str) -> Optional[str]:
    """Elite V2.2: Standardized VN Phone Validator (Zero-Any)."""
    if not phone: return None
    p = re.sub(r"[\s\.\-\+]", "", str(phone))
    if p.startswith("84"): p = "0" + p[2:]
    if len(p) == 10 and p.startswith("0"): return p
    return None

class LeadExtractor:
    """Refined Logic Engine for Lead-to-Order Conversion."""

    @staticmethod
    async def _hydrate_from_history(db: AsyncSession, session_id: str, lead: ExtractedLead) -> ExtractedLead:
        """Retrieve missing lead info from recent successful extractions in history."""
        from backend.database.models.system import SupportChatHistory
        from backend.utils.security import GeminiSecurity
        
        stmt = (
            select(SupportChatHistory)
            .where(SupportChatHistory.session_id == session_id)
            .order_by(SupportChatHistory.created_at.desc())
            .limit(10)
        )
        res = await db.execute(stmt)
        history = res.scalars().all()
        
        for h in history:
            if not lead.customer_phone and h.customer_phone:
                lead.customer_phone = h.customer_phone
            if not lead.customer_name and h.customer_name:
                lead.customer_name = h.customer_name
            if not lead.customer_address and h.role == "user":
                prev_msg = GeminiSecurity.decrypt(h.content or "").lower()
                if any(kw in prev_msg for kw in ["đường", "phố", "quận", "huyện", "/"]):
                    pass 

        return lead

    @staticmethod
    async def _resolve_product(db: AsyncSession, name: Optional[str] = None, slug: Optional[str] = None, tenant_id: str = "default") -> Optional[ProductBase]:
        """Fuzzy lookup product in DB. Scalar projection only (R110)."""
        try:
            if slug:
                stmt = select(ProductBase).where(ProductBase.slug == slug, ProductBase.tenant_id == tenant_id)
                p = (await db.execute(stmt)).scalar_one_or_none()
                if p: return p
                
                stmt_fuzzy = select(ProductBase).where(ProductBase.slug.ilike(f"%{slug}%"), ProductBase.tenant_id == tenant_id).limit(1)
                p_fuzzy = (await db.execute(stmt_fuzzy)).scalar_one_or_none()
                if p_fuzzy: return p_fuzzy
                
            if name:
                stmt_name = select(ProductBase).where(
                    or_(ProductBase.name.ilike(f"%{name}%"), ProductBase.slug.ilike(f"%{name.replace(' ', '-')}%")),
                    ProductBase.tenant_id == tenant_id
                ).limit(1)
                return (await db.execute(stmt_name)).scalar_one_or_none()
        except Exception as e:
            logger.warning("[LeadExtractor] _resolve_product fail: %s", e)
        return None

    @staticmethod
    def _apply_martial_combo_rules(qty: int) -> Tuple[int, Optional[str], bool]:
        """
        Elite V4.0: The Martial Combo Protocol (Sales & Upsell Intelligence).
        1 lọ -> 1 lọ
        2-3 lọ -> 3 lọ (Combo 2+1)
        4-5 lọ -> 5 lọ (Combo 4+1)
        > 5 lọ -> Contact support for bulk price
        """
        if qty <= 1: return 1, None, False
        if 2 <= qty <= 3: return 3, "combo-3", False
        if 4 <= qty <= 5: return 5, "combo-5", False
        return qty, None, True

    @staticmethod
    async def extract_and_convert(
        db: AsyncSession, 
        message: str, 
        session_id: str,
        current_product_slug: Optional[str] = None
    ) -> Optional[ExtractedLead]:
        """
        Atomic Extraction -> Validation -> Conversion Loop.
        """
        try:
            # 1. AI EXTRACTION (TrinityBridge Fast Tier)
            result = await trinity_bridge.run(_lead_extraction_agent, message, role="fast", session_id=session_id)
            
            # Elite V2.2: Standardized Result Extraction (Trust the Bridge)
            if isinstance(result, dict):
                lead = ExtractedLead.model_validate(result)
            elif isinstance(result, ExtractedLead):
                lead = result
            else:
                logger.warning(f"[LeadExtractor] Unknown result type: {type(result)}")
                return None

            # 2. DATA HYGIENE
            lead.customer_phone = validate_vietnam_phone(lead.customer_phone or "")
            
            # 🚀 2.0 HYDRATION FOR SHORT CONFIRMATIONS (Elite V2.5)
            # If message is "Ok" or AI didn't catch phone/address, try to get from history
            is_confirmation = message.lower().strip() in ["ok", "chốt", "đồng ý", "gửi đi", "vâng", "đúng rồi"]
            if is_confirmation or (lead.is_definite_purchase and (not lead.customer_phone or not lead.customer_address)):
                lead = await LeadExtractor._hydrate_from_history(db, session_id, lead)
                # Re-validate phone after hydration
                lead.customer_phone = validate_vietnam_phone(lead.customer_phone or "")

            # 2.1 Elite V2.5: Heuristic Purchase Force

            # If the staff explicitly says "Cho 1 đơn" or "Lên đơn", we FORCE definite purchase
            # to bypass any AI uncertainty.
            force_keywords = ["cho 1 đơn", "cho đơn", "lên đơn", "lấy 1 đơn", "gửi đơn"]
            if any(fw in message.lower() for fw in force_keywords):
                logger.info(f"🚀 [LeadExtractor] Heuristic Force: is_definite_purchase=True matched for '{message[:20]}...'")
                lead.is_definite_purchase = True

            # 2.1 ADDRESS RESOLUTION (Elite V2.2)
            if lead.customer_address:
                resolved: ResolvedLocation = await asyncio.to_thread(location_resolver.resolve, lead.customer_address)
                if resolved.is_valid:
                    # Construct a professional standardized address
                    std_addr = f"{resolved.house_number or ''} {resolved.street or ''}".strip()
                    if resolved.ward: std_addr += f", {resolved.ward}"
                    if resolved.district: std_addr += f", {resolved.district}"
                    if resolved.province: std_addr += f", {resolved.province}"
                    
                    lead.customer_address = std_addr
                    lead.shipping_days = resolved.shipping_days
                    logger.info(f"[LeadExtractor] Address Resolved: {lead.customer_address} (Score: {resolved.score}, Days: {lead.shipping_days})")
                else:
                    if resolved.possible_provinces:
                        lead.possible_provinces = resolved.possible_provinces
                        lead.is_definite_purchase = False # Pause to ask user
                        logger.info(f"[LeadExtractor] Address Ambiguous, found provinces: {lead.possible_provinces}")
                    logger.warning(f"[LeadExtractor] Address Resolution Low Confidence for: {lead.customer_address}")

            # 3. IDENTITY RESOLUTION (Elite V2.2)
            # Only resolve identity when we have a REAL phone — never use dummy fallback.
            from backend.database import current_tenant_id
            target_tenant = current_tenant_id.get() or "default"
            resolved_user = None
            if lead.customer_phone:
                resolved_user, is_new, prev_addr, addr_changed = await user_service.get_or_resolve_customer(
                    db=db, phone=lead.customer_phone,
                    name=lead.customer_name, current_address=lead.customer_address, tenant_id=target_tenant
                )
                lead.is_new_customer = is_new
                lead.previous_address = prev_addr
                lead.address_status = "NEW" if is_new else ("CHANGED" if addr_changed else "SAME")

            if not lead.is_definite_purchase or not lead.customer_phone:
                return lead

            # 4. CONVERSION (Martial Combo Protocol Execution)
            order_items: List[LeadOrderItemDict] = []
            total_amount: float = 0.0
            
            for item in lead.items:
                raw_qty: int = int(item.quantity)
                protocol_qty, combo_suffix, needs_contact = LeadExtractor._apply_martial_combo_rules(raw_qty)
                
                if needs_contact:
                    lead.is_definite_purchase = False
                    lead.needs_price_quote = True
                    return lead

                target_slug: Optional[str] = item.id or current_product_slug
                if combo_suffix and target_slug and "combo" not in target_slug:
                    target_slug = f"{combo_suffix}-{target_slug}"
                
                resolved_product = await LeadExtractor._resolve_product(
                    db, name=item.name if not combo_suffix else f"Combo {protocol_qty} {item.name}", 
                    slug=target_slug, tenant_id=target_tenant
                )
                
                p_id: str = str(resolved_product.id) if resolved_product else (target_slug or "unknown")
                price_per: float = float(resolved_product.discount_price or resolved_product.price) if resolved_product else float(item.price or 0.0)
                
                if resolved_product and "combo" in resolved_product.slug:
                    total_amount += price_per
                    order_items.append({"product_id": p_id, "name": resolved_product.name, "quantity": 1, "price": price_per})
                else:
                    total_amount += price_per * protocol_qty
                    order_items.append({"product_id": p_id, "name": resolved_product.name if resolved_product else item.name, "quantity": protocol_qty, "price": price_per})

            if not order_items and current_product_slug:
                # Fallback Heuristic (Surgical Regex Scan)
                qty_match = re.search(r"(\d+)\s*(lọ|chai|hộp|combo)", message.lower())
                raw_fallback_qty: int = int(qty_match.group(1)) if qty_match else 1
                protocol_qty, combo_suffix, needs_contact = LeadExtractor._apply_martial_combo_rules(raw_fallback_qty)
                
                if needs_contact:
                    lead.is_definite_purchase = False
                    lead.needs_price_quote = True
                    return lead
                    
                target_slug_fallback: str = current_product_slug
                if combo_suffix and "combo" not in target_slug_fallback:
                    target_slug_fallback = f"{combo_suffix}-{target_slug_fallback}"
                
                resolved_product_fallback = await LeadExtractor._resolve_product(db, slug=target_slug_fallback, tenant_id=target_tenant)
                price_per_fallback: float = float(resolved_product_fallback.discount_price or resolved_product_fallback.price) if resolved_product_fallback else 0.0
                
                if resolved_product_fallback and "combo" in resolved_product_fallback.slug:
                    order_items.append({"product_id": str(resolved_product_fallback.id), "name": resolved_product_fallback.name, "quantity": 1, "price": price_per_fallback})
                    total_amount = price_per_fallback
                else:
                    order_items.append({"product_id": current_product_slug, "name": resolved_product_fallback.name if resolved_product_fallback else "Sản phẩm", "quantity": protocol_qty, "price": price_per_fallback})
                    total_amount = price_per_fallback * protocol_qty

            if not order_items: return lead

            # Final precision rounding (Elite Financial Standard)
            total_amount = round(total_amount, 2)

            # Guard: resolved_user must exist to create order
            if not resolved_user:
                logger.warning("[LeadExtractor] No resolved user for order creation. Aborting.")
                return lead

            order_data = OrderCreateRequest(
                customer_name=lead.customer_name or "Khách chốt từ Chat",
                customer_email=resolved_user.email,
                customer_phone=lead.customer_phone,
                customer_address=lead.customer_address or "Chưa cung cấp địa chỉ",
                total_amount=total_amount,
                items=order_items,
            )
            
            created_order = await order_service.create_order(db_session=db, data=order_data, ip="0.0.0.0", ua="Helen-AI-Sales-Engine", user_id=str(resolved_user.id))
            await db.commit()
            lead.processed_order_id = str(getattr(created_order, "id", ""))
            logger.info(f"[LeadExtractor] ✅ Architectural Sweep OK: Order Created ({lead.processed_order_id})")
            return lead

        except Exception as e:
            logger.error(f"[LeadExtractor] Structural failure: {e}")
            return None

lead_extractor = LeadExtractor()
