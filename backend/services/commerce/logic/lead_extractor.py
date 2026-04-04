"""
Lead Extractor Service — Elite V2.2
===================================
Uses PydanticAI to extract structured lead data (Phone, Address, Order Items)
from unstructured chat messages.
"""
from __future__ import annotations
import logging
import re
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, or_
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.order import order_service
from backend.services.user_service import user_service
from backend.schemas.order import OrderCreateRequest, OrderItem
from backend.database.models import ProductBase

logger = logging.getLogger("api-gateway")

class LeadOrderItem(BaseModel):
    model_config = ConfigDict(strict=False)
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

import re

# Dedicated extraction agent (Elite V2.2 Specialist)
# Model is provided at runtime via trinity_bridge or direct call to avoid import-time key checks
_lead_extraction_agent = Agent(
    output_type=ExtractedLead,


    system_prompt=(
        "Bạn là một chuyên gia trích xuất đơn hàng tại Việt Nam (Elite Specialist). "
        "Nhiệm vụ của bạn là đọc nội dung hội thoại và trích xuất thông tin khách hàng muốn đặt hàng. "
        "QUY TẮC TRÍCH XUẤT NGHIÊM NGẶT:\n"
        "1. SĐT: Phải là số điện thoại Việt Nam hợp lệ (10 số). Bỏ qua các số giả hoặc không đủ chữ số.\n"
        "2. ĐỊA CHỈ: Trích xuất chi tiết nhất có thể. Cố gắng xác định: [Số nhà/Đường], [Phường/Xã], [Quận/Huyện], [Tỉnh/Thành phố].\n"
        "   - Nếu thiếu thông tin, hãy giữ nguyên phần thô mà khách cung cấp.\n"
        "3. SẢN PHẨM: Trích xuất tên và số lượng chính xác. Nếu khách nói 'combo', hãy ghi chú rõ trong tên sản phẩm.\n"
        "4. XÁC NHẬN CHỐT ĐƠN (is_definite_purchase):\n"
        "   - CHỈ ĐẶT True khi khách hàng có hành vi chốt đơn rõ ràng: Cung cấp SĐT + Địa chỉ, "
        "hoặc nói các câu khẳng định: 'gửi cho mình nhé', 'chốt đơn này', 'lấy cho mình bấy nhiêu'.\n"
        "   - ĐẶT False nếu khách chỉ hỏi giá, tư vấn, hoặc chưa cung cấp thông tin liên hệ.\n"
        "Mọi dữ liệu trích xuất phải trung thực với nội dung khách nói, không tự bịa thông tin."
    )
)

def validate_vietnam_phone(phone: str) -> Optional[str]:
    """Elite V2.2: Standardized VN Phone Validator (Handles +84, dots, spaces)."""
    if not phone: return None
    # Strip non-digits and common separators
    p = re.sub(r"[\s\.\-\+]", "", phone)
    
    # Handle international format +84 or 84
    if p.startswith("84"): 
        p = "0" + p[2:]
        
    # Standard VN mobile is 10 digits starting with 0
    if len(p) == 10 and p.startswith("0"):
        return p
    return None

class LeadExtractor:

    @staticmethod
    async def _resolve_product(db: AsyncSession, name: Optional[str] = None, slug: Optional[str] = None, tenant_id: str = "default"):
        """Fuzzy lookup product in DB by slug or name."""
        try:
            # 1. Exact slug match
            if slug:
                res = await db.execute(select(ProductBase).where(ProductBase.slug == slug, ProductBase.tenant_id == tenant_id))
                p = res.scalar_one_or_none()
                if p: return p

            # 2. Partial slug match (e.g. 'hoi-nach-hong-son' inside 'thuoc-dac-tri-hoi-nach-hong-son')
            if slug:
                res = await db.execute(
                    select(ProductBase).where(
                        ProductBase.slug.ilike(f"%{slug}%"),
                        ProductBase.tenant_id == tenant_id
                    ).limit(1)
                )
                p = res.scalar_one_or_none()
                if p: return p

            # 3. Fuzzy name match
            if name:
                res = await db.execute(
                    select(ProductBase).where(
                        or_(
                            ProductBase.name.ilike(f"%{name}%"),
                            ProductBase.slug.ilike(f"%{name.replace(' ', '-')}%")
                        ),
                        ProductBase.tenant_id == tenant_id
                    ).limit(1)
                )
                return res.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"[LeadExtractor] _resolve_product error: {e}")
        return None

    @staticmethod
    def _apply_combo_deals(product: ProductBase, quantity: int) -> tuple[Optional[dict], int]:
        """
        Apply the best matching combo deal from product_metadata.
        Returns: (matched_deal_dict, final_quantity)
        """
        try:
            metadata = product.product_metadata or {}
            deals = metadata.get("active_deals", [])
            if not deals: return None, quantity
            
            # Sort deals by quantity descending to match the largest possible combo
            deals = sorted(deals, key=lambda d: (d.get("buy_qty", 0) + d.get("get_qty", 0)), reverse=True)
            
            for deal in deals:
                buy_qty = deal.get("buy_qty", 0)
                get_qty = deal.get("get_qty", 0)
                total_combo_qty = buy_qty + get_qty
                
                # Rule 1: Exact match of total quantity (e.g. user asked for 3, and combo is buy 2 get 1)
                if quantity == total_combo_qty:
                    return deal, total_combo_qty
                
                # Rule 2: Semi-match (e.g. user asked for 2, and combo is buy 2 get 1)
                # We AUTO-UPGRADE to the combo to be helpful (Elite V2.2 Sales Strategy)
                if quantity == buy_qty and get_qty > 0:
                    return deal, total_combo_qty
        except:
            pass
        return None, quantity

    @staticmethod
    async def extract_and_convert(
        db: AsyncSession, 
        message: str, 
        session_id: str,
        current_product_slug: Optional[str] = None
    ) -> Optional[ExtractedLead]:
        """
        Runs the extraction and if a definite purchase is detected, creates a Draft Order.
        """
        try:
            # 1. AI Extraction (Elite V2.2: Using TrinityBridge for Dynamic Model Selection)
            result = await trinity_bridge.run(
                _lead_extraction_agent, 
                message, 
                role="fast",
                session_id=session_id
            )
            
            # Robust data extraction (Supports multiple pydantic-ai versions)
            lead = getattr(result, "data", result)
            if not isinstance(lead, ExtractedLead) and hasattr(result, "output"):
                lead = result.output
            
            if not isinstance(lead, ExtractedLead):
                logger.error(f"[LeadExtractor] Unexpected result type: {type(result)}. Attrs: {dir(result)}")
                return None


            # 2. Refined Validation (Elite V2.2)
            valid_phone = validate_vietnam_phone(lead.customer_phone or "")
            if not valid_phone:
                lead.customer_phone = None # Invalid phone, discard it
            else:
                lead.customer_phone = valid_phone

            # 3. IDENTITY RESOLUTION (Elite V2.2: User-First Protocol)
            from backend.database import current_tenant_id
            target_tenant = current_tenant_id.get() or "default"
            
            user, is_new, prev_addr, addr_changed = await user_service.get_or_resolve_customer(
                db=db,
                phone=lead.customer_phone or "0000000000",
                name=lead.customer_name,
                current_address=lead.customer_address,
                tenant_id=target_tenant
            )
            
            lead.is_new_customer = is_new
            lead.previous_address = prev_addr
            lead.address_status = "NEW" if is_new else ("CHANGED" if addr_changed else "SAME")

            if not lead.is_definite_purchase or not lead.customer_phone:
                return lead

            # 3. Convert and Enrich OrderItems (Elite V2.2: The Sales Expert)
            order_items: List[Dict[str, object]] = []
            total_amount = 0.0
            from backend.database import current_tenant_id
            target_tenant = current_tenant_id.get() or "default"
            
            for item in lead.items:
                # 🛡️ PRODUCT ENRICHMENT (Elite Protocol)
                # Try to resolve the actual product from DB
                resolved_product = await LeadExtractor._resolve_product(
                    db, 
                    name=item.name, 
                    slug=item.id or current_product_slug,
                    tenant_id=target_tenant
                )
                
                p_id = resolved_product.id if resolved_product else (item.id or current_product_slug or "unknown")
                qty = int(item.quantity)
                
                # Default price: Use Discount Price if available, otherwise Base Price, otherwise fallback
                base_price = (resolved_product.discount_price or resolved_product.price) if resolved_product else float(item.price or 0.0)
                
                # 🚀 COMBO MATCHING (Elite Sales Engine)
                # Apply active deals (e.g., Mua 2 Tặng 1) based on quantity
                final_item_price = base_price
                matched_deal, upgraded_qty = LeadExtractor._apply_combo_deals(resolved_product, qty) if resolved_product else (None, qty)
                
                # Update quantity if upgraded by combo (Elite V2.2 Professional Upsell)
                qty = upgraded_qty
                
                if matched_deal:
                    # Calculate effective price per unit for the total amount
                    # Total = fixed_price
                    total_amount += float(matched_deal.get("fixed_price", base_price * qty))
                    final_item_price = float(matched_deal.get("fixed_price", base_price * qty)) / qty
                else:
                    total_amount += base_price * qty

                order_items.append({
                    "product_id": p_id,
                    "name": resolved_product.name if resolved_product else (item.name or "Sản phẩm"),
                    "quantity": qty,
                    "price": final_item_price
                })

            if not order_items and current_product_slug:
                # Fallback to current viewed product
                resolved_product = await LeadExtractor._resolve_product(db, slug=current_product_slug, tenant_id=target_tenant)
                order_items.append({
                    "product_id": current_product_slug,
                    "name": resolved_product.name if resolved_product else "Sản phẩm đang xem",
                    "quantity": 1,
                    "price": (resolved_product.discount_price or resolved_product.price) if resolved_product else 0.0
                })
                total_amount = order_items[0]["price"]

            # 4. FINAL ORDER CONVERSION
            if not order_items:
                return lead

            order_data = OrderCreateRequest(
                customer_name=lead.customer_name or "Khách chốt từ Chat",
                customer_email=getattr(user, "email", None) or "helen.ai.auto@smartshop.test",
                customer_phone=lead.customer_phone,
                customer_address=lead.customer_address or "Chưa cung cấp địa chỉ",
                total_amount=total_amount,
                items=order_items,
            )
            
            created_order = await order_service.create_order(
                db_session=db,
                data=order_data,
                ip="0.0.0.0",  # Background process has no IP
                ua="Helen-AI-Sales-Engine",
                user_id=str(user.id)
            )
            # Atomic commit: ensure order is persisted before returning
            await db.commit()
            lead.processed_order_id = getattr(created_order, "id", None)
            logger.info(f"[LeadExtractor] ✅ Order {lead.processed_order_id} created for tenant '{target_tenant}'")
            return lead

        except Exception as e:
            logger.error(f"[LeadExtractor] Extraction failed: {e}")
            return None

lead_extractor = LeadExtractor()
