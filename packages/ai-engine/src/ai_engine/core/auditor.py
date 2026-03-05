import httpx
import os
from typing import Dict, Any

class AuditorAgent:
    """
    Auditor Agent: Thực thể AI chuyên biệt giám sát và phân tích tác động (Rule R11 - Phase 3).
    Nhiệm vụ: Đánh giá rủi ro của các bản ghi Draft trước khi Human-in-the-Loop phê duyệt.
    """
    
    def __init__(self):
        self.gateway_url = os.getenv("INTERNAL_API_URL", "http://api:8000")
        self.version = "1.0.0-auditor"

    async def analyze_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Thực hiện phân tích chuyên sâu về một bản ghi Draft.
        - Kiểm tra tính hợp lệ của payload.
        - Dự báo tác động hệ thống.
        - Chấm điểm rủi ro (Risk Scoring).
        """
        # Bước 1: Truy xuất chi tiết Draft từ Gateway/MCP
        draft_result = await self._call_mcp_tool("get_draft_analysis", {"draft_id": draft_id})
        
        if draft_result.get("status") != "success":
            return {
                "status": "error",
                "message": f"Không thể truy xuất dữ liệu Draft {draft_id}"
            }

        draft_data = draft_result["data"]
        payload = draft_data.get("payload", {})
        action = draft_data.get("action", "")
        target_model = draft_data.get("targetModel", "")

        # Bước 2: Chấm điểm rủi ro (Heuristic + Core Analysis)
        risk_score = 0
        insights = []

        if action == "DELETE":
            risk_score += 70
            insights.append("Hành động XÓA có rủi ro cao mất mát dữ liệu vĩnh viễn.")
        
        if target_model.lower() == "users":
            risk_score += 15
            insights.append("Tác động đến thực thể NGƯỜI DÙNG có thể ảnh hưởng đến trải nghiệm khách hàng.")

        if "all" in str(payload).lower() or not draft_data.get("targetId"):
            risk_score += 20
            insights.append("CẢNH BÁO: Hành động có phạm vi ảnh hưởng TOÀN BỘ (Bulk action).")

        # Bước 3: Dự báo tác động (Impact Prediction)
        impact = "LOW"
        if risk_score > 80:
            impact = "CRITICAL"
        elif risk_score > 50:
            impact = "MEDIUM"

        return {
            "draft_id": draft_id,
            "risk_score": min(risk_score, 100),
            "impact_level": impact,
            "insights": insights,
            "recommendation": "YÊU CẦU KIỂM TRA KỸ" if risk_score > 50 else "CÓ THỂ PHÊ DUYỆT",
            "audited_by": f"Auditor-Agent-v{self.version}"
        }

    async def _call_mcp_tool(self, name: str, arguments: dict) -> Dict[str, Any]:
        """Gọi công cụ MCP thông qua API Gateway"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/api/v1/mcp/call",
                    json={"name": name, "arguments": arguments},
                    timeout=10.0
                )
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e)}
