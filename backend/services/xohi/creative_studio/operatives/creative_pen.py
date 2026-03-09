from typing import List, Dict
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal

class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content.
    Hardened with "Golden Thread" (Approved metadata injection).
    V61.0: SSE-Ready and Protocol Compliant.
    """
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        step = kwargs.get("step")
        if step == 3:
            outline = await self.generate_outline(campaign)
            campaign.outline_data = outline.model_dump()
            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message="Outline generated based on Golden Thread.",
                data=campaign.outline_data
            )
        elif step == 4:
            content = await self.write_draft_stream(campaign)
            campaign.draft_content = content
            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message="Draft content generated.",
                data={"content_preview": content[:100]}
            )
        
        return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step} for CreativePen")

    async def generate_outline(self, campaign: ContentCampaign) -> ArticleOutline:
        """
        Step 3: Generate a technical outline based on Golden Thread.
        Ensures keywords are distributed across H2/H3.
        """
        # Hardened Logic: Inject gold_metadata (The Golden Thread)
        gold = campaign.gold_metadata or {}
        primary = gold.get("primary_keyword", "N/A")
        secondary = ", ".join(gold.get("secondary_keywords", []))
        
        # In production, this calls trinity_bridge with ArticleOutline schema
        # For now, we return a structured mock that respects the Golden Thread
        return ArticleOutline(sections=[
            {"heading": f"H1: {gold.get('title', 'Tiêu đề')}", "content": "Giới thiệu tổng quan về " + primary},
            {"heading": f"H2: Tại sao nên chọn {primary}", "content": "Phân tích lợi ích chuyên sâu. [IMAGE_1]"},
            {"heading": "H2: Các giải pháp hỗ trợ " + (gold.get("secondary_keywords", [""])[0]), "content": "Chi tiết kỹ thuật. [IMAGE_2]"},
            {"heading": "H2: Kết luận và Hướng đi", "content": "Lời kêu gọi hành động hiệu quả."}
        ])

    async def write_draft_stream(self, campaign: ContentCampaign) -> str:
        """
        Step 4: Generate full content.
        V61.0: In real implementation, this triggers an SSE Event via event_bus 
        to stream tokens to the frontend while saving the final result.
        """
        gold = campaign.gold_metadata
        outline = campaign.outline_data
        
        # Hardened Logic: Constant reminder of Golden Thread during generation
        # system_instruction = f"Bạn là {gold.get('persona')}. Bạn ĐANG viết bài về {gold.get('primary_keyword')}."
        
        # Mocking the result of a long-form generation
        return f"""
        <p>Chào mừng bạn đến với bài viết về <strong>{gold.get('primary_keyword')}</strong>.</p>
        <h2>Phần 1: Tổng quan</h2>
        <p>Đây là nội dung được chấp bút bởi AI theo phong cách {gold.get('persona')}. [IMAGE_1]</p>
        <h2>Phần 2: Lợi ích</h2>
        <p>Nội dung chi tiết đã được tối ưu SEO. [IMAGE_2]</p>
        """
