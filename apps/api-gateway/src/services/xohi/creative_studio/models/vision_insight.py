import logging
import os
from pydantic import BaseModel, Field
from typing import List
from src.database.models import ContentCampaign
from pydantic_ai import Agent
from ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

class TopicSeed(BaseModel):
    title: str = Field(description="Tiêu đề bài viết thu hút, chuẩn viral")
    primary_keyword: str = Field(description="Từ khóa chính quan trọng nhất")
    secondary_keywords: List[str] = Field(description="Danh sách 3-5 từ khóa phụ bổ trợ")
    persona: str = Field(description="Mô tả phong cách viết bài (e.g. trẻ trung, chuyên gia)")

VISION_PROMPT = """[ROLE] CHUYÊN GIA SEO CONTENT STRATEGY — Hệ thống XoHi Content Factory V62.1

[NHIỆM VỤ]
Phân tích chủ đề sếp đưa ra và đề xuất bộ Keywords SEO cho bài viết.

[LUẬT]
1. Tiêu đề phải giật tít nhưng KHÔNG clickbait rác, KHÔNG dùng emoji.
2. Từ khóa chính phải ngắn gọn (2-4 từ), có search volume cao.
3. Từ khóa phụ bổ trợ chủ đề chính, 3-5 từ khóa.
4. Persona: Mô tả giọng văn phù hợp đối tượng mục tiêu.
5. Trả về đúng JSON schema, KHÔNG thêm text ngoài."""

class VisionInsight:
    """
    Step 1: Analyze input (text/image) and generate the Golden Thread metadata.
    Uses PydanticAI Agent with Structured Output (TopicSeed).
    """
    def __init__(self):
        self.model_name = os.getenv("TIER2_MODEL", "gemini-2.0-flash")
        self.rotator = SmartKeyRotator()
        self.agent = Agent(
            output_type=TopicSeed,
            system_prompt=VISION_PROMPT
        )

    async def analyze_input(self, campaign: ContentCampaign) -> TopicSeed:
        """
        Uses AI to extract structured keywords from campaign.source_input.
        R85: Strict Structured Output via Pydantic.
        """
        from ai_engine.core.trinity_bridge import trinity_bridge

        prompt = f"Chủ đề bài viết: {campaign.source_input}"

        try:
            result = await trinity_bridge.run(
                self.agent,
                prompt,
            )
            return result.output
        except Exception as e:
            logger.error(f"[VisionInsight] AI failed, using fallback: {e}")
            # Fallback: Tạo keywords từ transcript gốc
            words = campaign.source_input.split()
            return TopicSeed(
                title=f"Khám phá {campaign.source_input}",
                primary_keyword=campaign.source_input[:50],
                secondary_keywords=words[:3] if len(words) >= 3 else words,
                persona="Chuyên gia, giọng văn thân thiện và chuyên nghiệp"
            )
