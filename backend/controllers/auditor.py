from litestar import Controller, get
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.auditor import AuditorAnalysisResponse
from backend.services.auditor_service import auditor_service

class AuditorController(Controller):
    path = "/api/v1/auditor"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/{draft_id:str}/analyze")
    async def analyze_draft(self, draft_id: str) -> AuditorAnalysisResponse:
        """
        Trigger Auditor Agent to analyze a specific draft (Phase 3).
        Trả về các chỉ số rủi ro và dự báo tác động.
        """
        return await auditor_service.analyze_draft(draft_id)
