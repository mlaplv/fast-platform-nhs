import logging
from backend.services.ai_engine.core.auditor import AuditorAgent
from backend.schemas.auditor import AuditorAnalysisResponse

logger = logging.getLogger("api-gateway")

class AuditorService:
    def __init__(self) -> None:
        self.auditor = AuditorAgent()

    async def analyze_draft(self, draft_id: str) -> AuditorAnalysisResponse:
        """
        Trigger Auditor Agent to analyze a specific draft (Phase 3).
        """
        data = await self.auditor.analyze_draft(draft_id)
        return AuditorAnalysisResponse.model_validate(data)

auditor_service = AuditorService()
