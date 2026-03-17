from litestar import Controller, get
from backend.services.ai_engine.auditor import AuditorService
from backend.middleware import PermissionGuard

class AuditorController(Controller):
    path = "/api/v1/auditor"
    guards = [PermissionGuard("sys:admin")]
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = AuditorService()

    @get("/{draft_id:str}/analyze")
    async def analyze_draft(self, draft_id: str) -> dict:
        """
        Trigger Auditor Agent to analyze a specific draft (Phase 3).
        Trả về các chỉ số rủi ro và dự báo tác động.
        """
        return await self.auditor.analyze_draft(draft_id)
