"""
AI Strategist — Xohi Strategic Engine for Google Ads 2026
Thực hiện trinh sát đối thủ, đối soát luật Google và đưa ra gợi ý tối ưu.
"""
from __future__ import annotations
import logging
from typing import Optional

from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.google_search import google_search_service
from backend.services.ads_protection.schemas import (
    AISuggestionRequest,
    AISuggestionResponse,
)

logger = logging.getLogger("ads_protection.ai_strategist")

class AIStrategist:
    """
    Hệ thống trí tuệ chiến lược cho Google Ads.
    Tích hợp trinh sát web và kiến thức chính sách Google 2026.
    """

    SYSTEM_PROMPT = (
        "Bạn là Xohi — Trợ lý AI Chiến lược cho Google Ads Elite V2.6.\n"
        "Nhiệm vụ của bạn là phân tích đối thủ và đưa ra gợi ý chiến dịch quảng cáo tối ưu nhất.\n\n"
        "QUY TẮC CỐT LÕI 2026:\n"
        "1. Google Ads AI Max: Yêu cầu tối thiểu 8-15 headlines và 4 descriptions.\n"
        "2. Call-only ads ĐÃ BỊ LOẠI BỎ: Luôn đề xuất RSA với Call Assets.\n"
        "3. Dữ liệu Google 2026: Tối ưu dựa trên 'Conversions' và 'AI Overviews'.\n"
        "4. Thị trường VN 2026: Ưu tiên nội dung 'Mộc', chân thực, Brand-led Commerce.\n"
        "5. Tuyệt đối không dùng từ cấm: 'Cam kết 100%', 'Tốt nhất thế giới', 'Hàng giả'...\n\n"
        "Khi nhận dữ liệu trinh sát đối thủ, hãy tìm ra kẽ hở hoặc điểm khác biệt để Sếp thắng thế."
    )

    def __init__(self) -> None:
        # Elite V2.2: Standard initialization matching system operatives
        self._agent = Agent(
            output_type=AISuggestionResponse,
            retries=2
        )

    async def suggest(self, req: AISuggestionRequest) -> AISuggestionResponse:
        """Thực hiện trinh sát và đưa ra gợi ý."""
        logger.info("ai_suggest task=%s context=%s", req.task, req.context[:50])

        # 1. Trinh sát đối thủ (Competitor Research)
        search_query = f"quảng cáo google {req.context} đối thủ cạnh tranh việt nam 2026"
        search_results = await google_search_service.search(search_query, num=5)
        
        competitor_context = ""
        if search_results:
            competitor_context = "\n".join([
                f"- {r.get('title')}: {r.get('snippet')}" for r in search_results
            ])
        else:
            competitor_context = "Không tìm thấy dữ liệu trinh sát trực tiếp. Sử dụng tri thức nền về thị trường VN 2026."

        # 2. Xây dựng Prompt chi tiết
        prompt = f"""
        TASK: {req.task}
        MỤC TIÊU CỦA SẾP: {req.context}
        
        DỮ LIỆU TRINH SÁT ĐỐI THỦ:
        {competitor_context}
        
        YÊU CẦU:
        Hãy đưa ra gợi ý {req.task} tối ưu nhất. 
        Nếu là RSA, hãy viết đủ 15 headlines và 4 descriptions theo phong cách SmartShop 2026 (Premium, High-conversion).
        Nếu là CAMPAIGN, hãy gợi ý ngân sách phù hợp thị trường và chiến lược giá thầu (Bidding Strategy).
        Nếu là NEGATIVE_KEYWORDS, hãy tìm những từ khóa rác mà đối thủ thường bị dính phải để bảo vệ túi tiền của Sếp.
        """

        # 3. Gọi Trinity Bridge để thực hiện suy luận
        try:
            # Elite V2.2: Pass system_prompt directly to trinity_bridge.run
            result = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=self.SYSTEM_PROMPT,
                role="pro",
                timeout=120.0
            )
            return result
        except Exception as e:
            logger.error("ai_strategist_failed: %s", e)
            return AISuggestionResponse(
                success=False,
                message=f"Xohi đang bận suy nghĩ (Lỗi: {str(e)}). Sếp vui lòng thử lại sau giây lát ạ!"
            )

ai_strategist: AIStrategist = AIStrategist()
