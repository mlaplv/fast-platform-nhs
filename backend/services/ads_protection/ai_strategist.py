"""
AI Strategist — Xohi Strategic Engine for Google Ads 2026
Thực hiện trinh sát đối thủ, đối soát luật Google và đưa ra gợi ý tối ưu.
"""
from __future__ import annotations
import logging
import httpx
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
        "QUY TẮC CỐT LÕI 2026 (SGE & SEO):\n"
        "1. SGE Compliance: Nội dung phải trả lời trực tiếp câu hỏi của người dùng, có cấu trúc dữ liệu (Schema.org) rõ ràng.\n"
        "2. Ads Quality Score: Landing Page phải khớp 100% với Keyword chủ đạo. H1 phải chứa Keyword.\n"
        "3. Tốc độ & LCP: Phải dưới 2.5s để không bị đánh tụt điểm.\n"
        "4. Google Ads AI Max: Yêu cầu tối thiểu 8-15 headlines và 4 descriptions.\n"
        "5. Thị trường VN 2026: Ưu tiên nội dung 'Mộc', chân thực, Brand-led Commerce.\n\n"
        "Khi nhận dữ liệu trinh sát đối thủ hoặc Landing Page, hãy tìm ra kẽ hở hoặc điểm cần tối ưu để Sếp thắng thế."
    )

    def __init__(self) -> None:
        self._agent = Agent(
            output_type=AISuggestionResponse,
            retries=2
        )

    async def _fetch_page(self, url: str) -> str:
        """Trinh sát nội dung Landing Page."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Xohi-Neural-Scout/1.0"})
                if resp.status_code == 200:
                    # Lấy text cơ bản từ HTML (rất thô sơ để AI dễ đọc)
                    from lxml import html
                    tree = html.fromstring(resp.content)
                    # Xóa script/style
                    for s in tree.xpath("//script|//style"):
                        s.getparent().remove(s)
                    
                    title = tree.xpath("//title/text()")
                    h1 = tree.xpath("//h1//text()")
                    text = tree.text_content()
                    return f"TITLE: {title}\nH1: {h1}\nCONTENT_PREVIEW: {text[:2000]}"
                return f"Lỗi truy cập Landing Page (Status: {resp.status_code})"
        except Exception as e:
            return f"Lỗi kết nối trinh sát: {str(e)}"

    async def suggest(self, req: AISuggestionRequest) -> AISuggestionResponse:
        """Thực hiện trinh sát và đưa ra gợi ý."""
        logger.info("ai_suggest task=%s context=%s", req.task, req.context[:50])

        target_url = ""
        page_content = ""

        # Nếu task là AUDIT hoặc có URL trong context, thực hiện trinh sát URL
        if req.task == "AUDIT_LANDING_PAGE" or "http" in req.context:
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', req.context)
            if urls:
                target_url = urls[0]
                page_content = await self._fetch_page(target_url)

        # 1. Trinh sát đối thủ (Competitor Research)
        search_query = f"quảng cáo google {req.context} đối thủ cạnh tranh việt nam 2026"
        search_results = await google_search_service.search(search_query, num=3)
        
        competitor_context = ""
        if search_results:
            competitor_context = "\n".join([
                f"- {r.get('title')}: {r.get('snippet')}" for r in search_results
            ])
        else:
            competitor_context = "Không tìm thấy dữ liệu trinh sát trực tiếp."

        # 2. Xây dựng Prompt chi tiết
        prompt = f"""
        TASK: {req.task}
        MỤC TIÊU/NGỮ CẢNH: {req.context}
        
        {f"DỮ LIỆU TRINH SÁT TRANG ĐÍCH ({target_url}):" if target_url else ""}
        {page_content if target_url else ""}

        DỮ LIỆU TRINH SÁT ĐỐI THỦ:
        {competitor_context}
        
        YÊU CẦU:
        Hãy đưa ra gợi ý {req.task} tối ưu nhất. 
        Nếu là AUDIT_LANDING_PAGE, hãy:
        1. Chấm điểm (0-100) cho các trường: seo_score, sge_score, và quality_score.
        2. Đưa ra các hành động SỬA LỖI cụ thể trong phần 'message' để đạt điểm tối đa.
        3. Phân tích xem trang đã sẵn sàng cho SGE (Search Generative Experience) chưa.
        """

        # 3. Gọi Trinity Bridge để thực hiện suy luận
        try:
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
