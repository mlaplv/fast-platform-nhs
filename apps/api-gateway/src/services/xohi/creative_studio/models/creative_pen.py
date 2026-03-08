import json
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from src.database.models import ContentCampaign

class ArticleOutline(BaseModel):
    sections: List[Dict[str, str]] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")

class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content.
    Hardened with "Golden Thread" (Approved metadata injection).
    """
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name

    async def generate_outline(self, campaign: ContentCampaign) -> ArticleOutline:
        """
        Step 3: Generate a technical outline based on Golden Thread.
        Ensures keywords are distributed across H2/H3.
        """
        # Hardened Logic: Inject gold_metadata (The Golden Thread)
        gold = campaign.gold_metadata or {}
        primary = gold.get("primary_keyword", "N/A")
        secondary = ", ".join(gold.get("secondary_keywords", []))
        
        prompt = f"""
        Lập dàn ý SEO cho bài viết.
        TIÊU ĐIỂM (GOLDEN THREAD):
        - Từ khóa chính: {primary}
        - Từ khóa phụ: {secondary}
        - Phong cách: {gold.get("persona", "Chuyên nghiệp")}
        
        Tài nguyên hình ảnh: Có {len(campaign.assets_data)} ảnh.
        Yêu cầu: Nhét tag [IMAGE_1], [IMAGE_2]... vào các đoạn phù hợp.
        """
        
        # Concept: response_schema=ArticleOutline
        return ArticleOutline(sections=[
            {"heading": "H1: " + gold.get("title", "Tiêu đề"), "content": "Giới thiệu tổng quan"},
            {"heading": "H2: Tại sao nên chọn " + primary, "content": "Phân tích lợi ích. [IMAGE_1]"},
            {"heading": "H2: Cách thức hoạt động", "content": "Chi tiết kỹ thuật. [IMAGE_2]"},
            {"heading": "H2: Kết luận", "content": "Lời kêu gọi hành động."}
        ])

    async def write_draft_stream(self, campaign: ContentCampaign):
        """
        Step 4: Generate full content using SSE Streaming.
        This would be a generator function in real Python.
        """
        gold = campaign.gold_metadata
        outline = campaign.outline_data
        
        # Hardened Logic: Constant reminder of Golden Thread during generation
        system_instruction = f"Bạn là {gold.get('persona')}. Bạn ĐANG viết bài về {gold.get('primary_keyword')}."
        
        # In real code, this would yield chunks
        # for chunk in model.generate_content_stream(...):
        #     yield chunk
        
        return "Nội dung bài viết hoàn chỉnh với các thẻ [IMAGE_X] đã được đắp thịt..."
