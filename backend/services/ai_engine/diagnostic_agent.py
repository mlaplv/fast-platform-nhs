import logging
import json
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from pydantic_ai import Agent # type: ignore
from pydantic_ai.models.google import GoogleModel # type: ignore
from pydantic_ai.providers.google import GoogleProvider # type: ignore
from backend.services.ai_engine.core.key_loader import KeyLoaderMixin # type: ignore

import redis.asyncio as _redis # type: ignore
from sqlalchemy import select
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

class DiagnosticAgent(KeyLoaderMixin):
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client
        self.client = redis_client
        self.keys: List[str] = []
        self.index: int = 0
        self._use_redis: bool = redis_client is not None
        self.DISCOVERED_MODELS_KEY = "system:discovered_models"
        self.MAX_COOLDOWN = 3600

    async def get_fast_model(self) -> str:
        """Viral 2026: Auto-select best 'flash' model from discovery."""
        discovered = await self.get_discovered_models()
        if not discovered: return "gemini-2.0-flash"
        
        flash_models = [m for m in discovered if "flash" in m.lower()]
        if not flash_models: return "gemini-2.0-flash"
        
        flash_models.sort(reverse=True)
        return str(flash_models[0])

    async def analyze(self, product_name: str, quiz_data: List[Dict[str, str]]) -> Optional[DiagnosticReport]:
        """Viral 2026: Agentic Clinical Analysis."""
        try:
            # 1. Load keys if needed
            if not getattr(self, 'keys', None):
                await self.load_keys()
            
            api_key = self.get_next_key()
            if not api_key:
                logger.warning("[DiagnosticAgent] No API Key available")
                return None

            # 2. Setup AI
            model_name = await self.get_fast_model()
            provider = GoogleProvider(api_key=api_key)
            model = GoogleModel(model_name, provider=provider)
            
            # 3. Fetch Dynamic Promotions from DB (Elite V2.2 Zero-Hardcode)
            promos_text = "Hiện chưa có chương trình quà tặng."
            async with async_session_maker() as session:
                query = select(ProductBase).where(ProductBase.name == product_name)
                product = (await session.execute(query)).scalar_one_or_none()
                if product and product.product_metadata:
                    deals = product.product_metadata.get("active_deals", [])
                    if deals:
                        promos_text = "\n".join([f"- {d.get('label')}: Mua {d.get('buy_qty')} nhận thêm {d.get('get_qty')}" for d in deals])

            agent = Agent(
                model,
                output_type=DiagnosticReport,
                system_prompt=(
                    f"Bạn là Chuyên gia Chẩn đoán Lâm sàng cho sản phẩm '{product_name}'.\n"
                    "Nhiệm vụ: Phân tích Quiz Data và đưa ra PHÁC ĐỒ ĐIỀU TRỊ CHUẨN ELITE 2026.\n\n"
                    f"CHƯƠNG TRÌNH KHUYẾN MÃI HIỆN CÓ (Đọc từ Admin):\n{promos_text}\n\n"
                    "QUY TẮC CHẤM ĐIỂM & GỢI Ý LIỆU TRÌNH:\n"
                    "1. MỨC ĐỘ NHẸ: Mùi mới bị < 3 tháng, mồ hôi nhẹ. -> Đề xuất 1 lọ.\n"
                    "2. MỨC ĐỘ TRUNG BÌNH: Mùi hàng ngày, áo ố nhẹ. -> Đề xuất Mua 2 Tặng 1 (nếu có trong danh sách khuyến mãi).\n"
                    "3. MỨC ĐỘ NẶNG: Mùi nồng nặc, bị > 1 năm, lờn thuốc. -> Đề xuất Mua 4 Tặng 2 (nếu có trong danh sách khuyến mãi).\n\n"
                    "YÊU CẦU TRÌNH BÀY:\n"
                    "- Ngôn ngữ: Tiếng Việt chuyên gia, thâm thúy, tin cậy.\n"
                    "- Ưu tiên đề xuất theo gói khuyến mãi cao nhất phù hợp với mức độ bệnh để khách hàng dùng đủ ngày.\n"
                    "- Phải điền chính xác trường 'promotion_label' nếu áp dụng gói quà tặng."
                )
            )

            # 4. Execution
            prompt = f"Dữ liệu khảo sát khách hàng (Quiz Data): {json.dumps(quiz_data, ensure_ascii=False)}"
            result = await agent.run(prompt)
            return result.output
            
        except Exception as e:
            logger.error(f"[DiagnosticAgent] Analysis failed: {e}")
            return None
