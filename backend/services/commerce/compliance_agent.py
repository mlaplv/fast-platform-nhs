from __future__ import annotations
import logging
import json
import httpx
from typing import Optional, Dict
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

class ComplianceExtraction(BaseModel):
    notification_no: Optional[str] = Field(None, description="Số tiếp nhận phiếu công bố (VD: 259062/24/CBMP-QLD)")
    notification_date: Optional[str] = Field(None, description="Ngày cấp phiếu (YYYY-MM-DD)")
    authority: Optional[str] = Field(None, description="Cơ quan cấp phép (VD: Cục Quản lý Dược - Bộ Y tế)")

class ComplianceVisionAgent:
    """Agentic Vision for Regulatory Compliance (Elite V2.2)."""
    
    def __init__(self) -> None:
        self.agent = Agent(
            output_type=ComplianceExtraction,
            system_prompt=(
                "Bạn là chuyên gia thẩm định hồ sơ pháp lý mỹ phẩm tại Việt Nam. "
                "Nhiệm vụ của bạn là trích xuất các thông tin then chốt từ ẢNH 'PHIẾU CÔNG BỐ SẢN PHẨM MỸ PHẨM'. "
                "Các thông tin cần tìm: \n"
                "1. Số tiếp nhận phiếu công bố: Thường nằm ở góc trên hoặc phần đóng dấu (VD: 12345/23/CBMP-QLD).\n"
                "2. Ngày tiếp nhận/cấp: Ngày mà cơ quan quản lý đóng dấu xác nhận.\n"
                "3. Cơ quan cấp phép: Thường là Cục Quản lý Dược hoặc Sở Y tế.\n"
                "Trả về định dạng JSON chuẩn xác."
            )
        )

    async def scan_image(self, image_url: str) -> ComplianceExtraction:
        """Surgical Image Analysis via Trinity Bridge."""
        logger.info(f"🔍 [ComplianceVisionAgent] Analyzing image: {image_url}")
        
        # Elite V2.2: Handle both external URLs and local relative paths
        try:
            if not image_url.startswith("http"):
                import os
                # Try to resolve local path
                local_path = next((p for base in ["frontend/static", "."] if os.path.isfile(p := os.path.join(base, image_url.lstrip("/")))), None)
                if not local_path:
                    raise FileNotFoundError(f"Local file not found for: {image_url}")
                with open(local_path, "rb") as f:
                    image_data = f.read()
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(image_url)
                    resp.raise_for_status()
                    image_data = resp.content
        except Exception as e:
            logger.error(f"❌ [ComplianceVisionAgent] Image fetch failed: {e}")
            raise Exception(f"Không thể tải ảnh từ URL: {image_url}")

        # Construct prompt with image attachment support (if TrinityBridge/PydanticAI supports it)
        # For now, we use a prompt that describes the task. 
        # Note: trinity_bridge needs to be updated or used carefully for binary data.
        from pydantic_ai.messages import BinaryContent
        
        # Determine media type based on URL/Path extension
        media_type = "image/jpeg"
        if image_url.lower().endswith(".webp"):
            media_type = "image/webp"
        elif image_url.lower().endswith(".png"):
            media_type = "image/png"
            
        prompt = [
            "Hãy trích xuất thông tin từ ảnh này:",
            BinaryContent(data=image_data, media_type=media_type)
        ]
        
        try:
            # Elite V2.2: Specify 'vision' role for precise OCR routing
            result = await trinity_bridge.run(self.agent, prompt, role="vision")
            return result
        except Exception as e:
            logger.error(f"❌ [ComplianceVisionAgent] AI Scan failed: {e}")
            return ComplianceExtraction()

compliance_vision_agent = ComplianceVisionAgent()
