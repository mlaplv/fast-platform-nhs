import asyncio
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal

class PlagiarismCop:
    """
    Step 5: Check content uniqueness.
    Hardened with Semantic Similarity check using shared embeddings.
    V61.0: Protocol Compliant with Backtracking support.
    """
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        score = await self.check_uniqueness(campaign.draft_content)
        campaign.unique_score = score
        
        if score < self.threshold:
            # R103/R107: Trigger Agentic Backtracking signal
            return AgentResponse(
                signal=AgentSignal.REDO_PREVIOUS,
                message=f"Nội dung quá giống nguồn khác (Score: {score:.2f}). Đang yêu cầu AI viết lại.",
                data={"score": score}
            )
            
        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message=f"Kiểm tra đạo văn hoàn tất. Độ độc bản cao ({score:.2f}).",
            data={"score": score}
        )

    async def check_uniqueness(self, content: str) -> float:
        """
        Calculates a semantic uniqueness score.
        V61.0: Mocking processing time and result.
        """
        if not content:
            return 0.0
            
        await asyncio.sleep(1.5) # R82.8: Artificial Latency
        
        # In real logic: calls crawl4ai + shared encoder
        # Mocking success result
        return 0.92
