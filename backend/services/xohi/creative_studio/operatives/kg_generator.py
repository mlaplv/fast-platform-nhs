import json
import logging
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

# ══════════════════════════════════════════════════════════════
# ELITE V2.2: KNOWLEDGE GRAPH MODELS (SGE 2026)
# ══════════════════════════════════════════════════════════════

class Entity(BaseModel):
    name: str = Field(..., description="Tên thực thể (VD: Retinol, Da nhạy cảm)")
    type: str = Field(..., description="Loại thực thể: Ingredient, Benefit, SkinType, Device, Routine")
    description: str = Field(..., description="Mô tả ngắn gọn vai trò của thực thể trong ngữ cảnh này")

class KnowledgeGraph(BaseModel):
    """Cấu trúc đồ thị tri thức để Google SGE trích xuất"""
    entities: List[Entity] = Field(..., description="Danh sách các thực thể quan trọng nhất")
    main_takeaway: str = Field(..., description="Thông điệp cốt lõi (1 câu) cho AI Overview")
    expert_claim: str = Field(..., description="Khẳng định chuyên môn có bằng chứng")

class KnowledgeGraphGenerator(BaseAgentOperative):
    """
    Elite V2.2: Knowledge Graph Generator (KGG).
    Biến nội dung Review/Article thành thực thể dữ liệu có cấu trúc cho AI Search.
    """
    agent_id_class = "kg_generator"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="kg_generator")
        # Pydantic V2 structured output agent
        self._agent = Agent(
            model=None, # Use Trinity Bridge model settings
            output_type=KnowledgeGraph,
            system_prompt=(
                "Bạn là Chuyên gia Kiến trúc Tri thức (Knowledge Architect) cấp cao. "
                "Nhiệm vụ: Trích xuất các thực thể thực tế (Entities) từ nội dung để xây dựng Knowledge Graph cho Google SGE. "
                "Quy tắc:\n"
                "1. CHỈ trích xuất thông tin có thật trong văn bản.\n"
                "2. Phân loại thực thể chính xác (Ingredient, Benefit, SkinType, v.v.).\n"
                "3. 'main_takeaway' phải cực kỳ súc tích, mang tính kết luận chuyên môn.\n"
                "4. KHÔNG thêm thắt thông tin nằm ngoài nội dung được cung cấp."
            )
        )

    async def chat(self, request: object, **kwargs: object) -> dict:
        """
        Trích xuất Knowledge Graph từ content.
        """
        content = str(kwargs.get("content", ""))
        topic = str(kwargs.get("topic", ""))
        
        if not content:
            return {"entities": [], "main_takeaway": "Nội dung trống.", "expert_claim": ""}

        prompt = f"[TIÊU ĐIỂM]: {topic}\n\n[NỘI DUNG]:\n{content}"

        try:
            # CNS V2.2: Structured execution via Trinity Bridge
            response = await trinity_bridge.run(
                self._agent, 
                prompt,
                role="pro",
                timeout=90.0,
                model_settings={"temperature": 0.1} # High precision for entity extraction
            )
            
            # response.data is already a KnowledgeGraph model
            result = getattr(response, "data", response)
            if isinstance(result, KnowledgeGraph):
                return result.model_dump()
            
            # Fallback if bridge returns raw str (shouldn't happen with result_type)
            return json.loads(str(result))
            
        except Exception as exc:
            logger.error(f"[KGG] Lỗi trích xuất: {exc}")
            return {"entities": [], "main_takeaway": "Lỗi xử lý thực thể.", "expert_claim": str(exc)}

# Heritage Backdoor
async def generate_knowledge_graph(content: str, topic: str = "") -> dict:
    generator = KnowledgeGraphGenerator()
    return await generator.chat(None, content=content, topic=topic)
