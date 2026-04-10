import logging
import json
from typing import List, Optional, Dict, cast
from pydantic import BaseModel, Field
from pydantic_ai import Agent # type: ignore
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge # type: ignore

import redis.asyncio as _redis # type: ignore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import async_session_maker # type: ignore
from backend.database.models.commerce import ProductBase # type: ignore

logger = logging.getLogger("api-gateway")

class SuggestedProduct(BaseModel):
    id: str
    name: str
    reason: str

class DiagnosticReport(BaseModel):
    severity: str = Field(description="Mức độ biểu hiện: ví dụ Nhẹ, Trung bình, Nặng")
    analysis: str = Field(description="Phân tích chuyên sâu về tình trạng của khách hàng (tiếng Việt)")
    reasoning: str = Field(description="Lập luận y khoa đằng sau chẩn đoán này (tiếng Việt)")
    recommendation: str = Field(description="Lời khuyên về lối sống và cách sử dụng sản phẩm (tiếng Việt)")
    suggested_products: List[SuggestedProduct] = Field(description="Danh sách sản phẩm gợi ý")
    quantity: int = Field(description="Số lượng sản phẩm khách cần mua (không tính quà tặng)")
    promotion_label: Optional[str] = Field(description="Nhãn khuyến mãi: ví dụ 'MUA 2 TẶNG 1' hoặc 'MUA 4 TẶNG 2'")

class DiagnosticAgent:
    """Elite V2.2: AI Diagnostic Agent using TrinityBridge."""
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client

    async def analyze(self, db_session: AsyncSession, product_name: str, quiz_data: List[Dict[str, str]]) -> Optional[DiagnosticReport]:
        """Viral 2026: Agentic Clinical Analysis via Centralized Bridge."""
        try:
            # 1. Fetch Dynamic Promotions from DB (Elite V2.2 Zero-Hardcode)
            promos_text = "Hiện chưa có chương trình quà tặng."
            query = select(ProductBase).where(ProductBase.name == product_name)
            product = (await db_session.execute(query)).scalar_one_or_none()
            if product and product.product_metadata:
                deals = product.product_metadata.get("active_deals", [])
                if deals:
                    promos_text = "\n".join([f"- {d.get('label')}: Mua {d.get('buy_qty')} nhận thêm {d.get('get_qty')}" for d in deals])

            agent = Agent(
                output_type=DiagnosticReport,
            )
            
            system_prompt = (
                f"Bạn là Chuyên gia Chẩn đoán Lâm sàng chuyên biệt cho sản phẩm '{product_name}'.\n"
                "Nhiệm vụ: Phân tích dữ liệu khảo sát (Quiz Data) và thiết lập PHÁC ĐỒ ĐIỀU TRỊ CHUẨN NHẬT BẢN.\n\n"
                f"DỮ LIỆU SẢN PHẨM HIỆN TẠI:\n"
                f"- Mô tả: {product.description if product else 'Sản phẩm dưỡng da cao cấp.'}\n"
                f"- Chương trình ưu đãi: {promos_text}\n\n"
                "QUY TẮC PHÂN TÍCH & ĐỀ XUẤT:\n"
                "1. Dựa trên mức độ nghiêm trọng (Nhẹ, Trung bình, Nặng) của sắc tố hắc tố Melanin để đưa ra số lượng sử dụng phù hợp.\n"
                "2. ĐỀ XUẤT PHẢI TẬP TRUNG vào hiệu quả làm sáng da, khử thâm và tái tạo vùng nhạy cảm.\n"
                "3. Luôn ưu tiên áp dụng các gói khuyến mãi có lợi nhất cho khách hàng dựa trên chương trình ưu đãi hiện có.\n\n"
                "YÊU CẦU TRÌNH BÀY:\n"
                "- Ngôn ngữ: Tiếng Việt chuyên gia, súc tích, mang tính thuyết phục cao.\n"
                "- Phải điền chính xác trường 'promotion_label' nếu có ưu đãi phù hợp (ví dụ: 'MUA 2 TẶNG 1')."
            )

            prompt = f"Dữ liệu khảo sát khách hàng (Quiz Data): {json.dumps(quiz_data, ensure_ascii=False)}"
            
            # Utilize the centralized bridge for military-grade stability
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                system_prompt=system_prompt,
                role="fast", # Use 'fast' role for quick diagnostic responses
                timeout=45.0
            )
            
            # TrinityBridge already extracts .data/.output, so we return the result directly
            if result:
                return cast(DiagnosticReport, result)
            return None
            
        except Exception as e:
            logger.error(f"[DiagnosticAgent] Fatal Error: {e}")
            return None
