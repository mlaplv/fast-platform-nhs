"""
Lead Extractor Service — Elite V2.2
===================================
Uses PydanticAI to extract structured lead data (Phone, Address, Order Items)
from unstructured chat messages.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.order import order_service
from backend.schemas.order import OrderCreateRequest, OrderItem

logger = logging.getLogger("api-gateway")

class ExtractedLead(BaseModel):
    model_config = ConfigDict(strict=False)
    customer_name: Optional[str] = Field(None, description="Tên khách hàng nếu có")
    customer_phone: Optional[str] = Field(None, description="Số điện thoại Việt Nam (10 số)")
    customer_address: Optional[str] = Field(None, description="Địa chỉ giao hàng chi tiết")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách sản phẩm: [{name, quantity, price}]")
    is_definite_purchase: bool = Field(False, description="True nếu khách hàng đã xác nhận chốt đơn hoặc đồng ý mua")

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
            # 1. AI Extraction (Elite V2.2: Pass model explicitly at runtime)
            result = await _lead_extraction_agent.run(message, model='google-gla:gemini-1.5-flash')
            lead: ExtractedLead = result.data


            # 2. Refined Validation (Elite V2.2)
            valid_phone = validate_vietnam_phone(lead.customer_phone or "")
            if not valid_phone:
                lead.customer_phone = None # Invalid phone, discard it
            else:
                lead.customer_phone = valid_phone

            if not lead.is_definite_purchase or not lead.customer_phone:
                return lead

            # 3. Convert to OrderItems (Elite V2.2: Must be dicts for OrderCreateRequest)
            order_items: List[Dict[str, Any]] = []
            total_amount = 0.0
            
            for item in lead.items:
                p_id = str(item.get("id", current_product_slug or "unknown"))
                qty = int(item.get("quantity", 1))
                price = float(item.get("price", 0))
                
                order_items.append({
                    "product_id": p_id,
                    "name": item.get("name", "Sản phẩm"),
                    "quantity": qty,
                    "price": price
                })
                total_amount += price * qty

            if not order_items and current_product_slug:
                # Fallback to current viewed product if no items extracted but purchase intent is clear
                order_items.append({
                    "product_id": current_product_slug,
                    "name": "Sản phẩm đang xem",
                    "quantity": 1,
                    "price": 0.0
                })

            # 4. Create Draft Order (Initial status PENDING with a 'DRAFT' flag in metadata)
            if order_items:
                draft_data = OrderCreateRequest(
                    customer_name=lead.customer_name or "Khách chốt từ Chat",
                    customer_email="helen.ai.auto@smartshop.test", # Mandatory for Elite V2.2
                    customer_phone=lead.customer_phone,
                    customer_address=lead.customer_address or "Chưa cung cấp địa chỉ",
                    items=order_items,
                    total_amount=total_amount
                )

                
                # Use order_service to persist
                # Note: IP and UA are placeholder for AI-triggered orders
                await order_service.create_order(
                    db_session=db,
                    data=draft_data,
                    ip="0.0.0.0",
                    ua="Helen-AI-AutoDraft"
                )
                logger.info(f"[LeadExtractor] Created Auto-Draft for session {session_id}")
            
            return lead

        except Exception as e:
            logger.error(f"[LeadExtractor] Extraction failed: {e}")
            return None

lead_extractor = LeadExtractor()
