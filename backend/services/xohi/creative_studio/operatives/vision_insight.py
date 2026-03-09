import logging
import os
import uuid
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from pydantic_ai import Agent
from backend.services.ai_engine.core.key_rotator import SmartKeyRotator
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, AgentResponse, AgentSignal

logger = logging.getLogger("api-gateway")

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

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        seed = await self.analyze_input(campaign)
        
        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message="Topic analyzed successfully.",
            data=seed.model_dump()
        )

    async def analyze_input(self, campaign: ContentCampaign) -> TopicSeed:
        """
        Uses AI to extract structured keywords from campaign.source_input.
        R85: Strict Structured Output via Pydantic.
        """
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        prompt = f"Chủ đề bài viết: {campaign.source_input}"

        try:
            # R101/R106: Using trinity_bridge for managed AI calls
            result = await trinity_bridge.run(
                self.agent,
                prompt,
            )
            # result.data is the TopicSeed instance when using PydanticAI
            return result.data if hasattr(result, "data") else result.output
        except Exception as e:
            logger.error(f"[VisionInsight] AI failed, using fallback: {e}")
            # Fallback: Tạo keywords từ transcript gốc (Graceful Degradation R103)
            words = campaign.source_input.split()
            return TopicSeed(
                title=f"Khám phá {campaign.source_input}",
                primary_keyword=campaign.source_input[:50],
                secondary_keywords=words[:3] if len(words) >= 3 else words,
                persona="Chuyên gia, giọng văn thân thiện và chuyên nghiệp"
            )
