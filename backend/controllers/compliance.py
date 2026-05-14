from __future__ import annotations
import logging
from typing import Dict
from litestar import Controller, post
from backend.services.commerce.compliance_agent import compliance_vision_agent
from backend.schemas.common import SuccessResponse
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class ComplianceController(Controller):
    """Elite V2.2: Compliance Management & AI Intelligence."""
    path = "/api/v1/admin/compliance"
    guards = [PermissionGuard(PermissionEnum.PRODUCT_WRITE)]

    @post("/scan-image")
    async def scan_compliance_image(self, data: Dict[str, str]) -> SuccessResponse:
        """Surgical OCR & Data Extraction from Regulatory Images."""
        image_url = data.get("image_url")
        if not image_url:
            return SuccessResponse(message="Thiếu URL ảnh", data={}, success=False)
            
        try:
            result = await compliance_vision_agent.scan_image(image_url)
            return SuccessResponse(
                message="Trích xuất thành công",
                data={
                    "notification_no": result.notification_no,
                    "notification_date": result.notification_date,
                    "authority": result.authority
                }
            )
        except Exception as e:
            logger.error(f"❌ [ComplianceController] Scan failed: {e}")
            return SuccessResponse(message=str(e), data={}, success=False)
