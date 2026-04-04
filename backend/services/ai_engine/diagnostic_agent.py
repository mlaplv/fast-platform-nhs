import logging
import json
from typing import List, Optional, Dict
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
                f"Bạn là Chuyên gia Chẩn đoán Lâm sàng cho sản phẩm '{product_name}'.\n"
                "Nhiệm vụ: Phân tích Quiz Data và đưa ra PHÁC ĐỒ ĐIỀU TRỊ CHUẨN ELITE 2026.\n\n"
                f"CHƯƠNG TRÌNH KHUYẾN MÃI HIỆN CÓ (Đọc từ Admin):\n{promos_text}\n\n"
                "QUY TẮC CHẤM ĐIỂM & GỢI Ý LIỆU TRÌNH:\n"
                "1. MỨC ĐỘ NHẸ: Mùi mới bị < 3 tháng, mồ hôi nhẹ. -> Đề xuất 1 lọ.\n"
                "2. MỨC ĐỘ TRUNG BÌNH: Mùi hàng ngày, áo ố nhẹ. -> Đề xuất Mua 2 Tặng 1.\n"
                "3. MỨC ĐỘ NẶNG: Mùi nồng nặc, bị > 1 năm, lờn thuốc. -> Đề xuất Mua 4 Tặng 2.\n\n"
                "YÊU CẦU TRÌNH BÀY:\n"
                "- Ngôn ngữ: Tiếng Việt chuyên gia, thâm thúy, tin cậy.\n"
                "- Ưu tiên đề xuất theo gói khuyến mãi cao nhất phù hợp với mức độ bệnh.\n"
                "- Phải điền chính xác trường 'promotion_label' (ví dụ: 'MUA 2 TẶNG 1')."
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
            
            if result:
                return getattr(result, "data", getattr(result, "output", None))
            return None
            
        except Exception as e:
            logger.error(f"[DiagnosticAgent] Fatal Error: {e}")
            return None
