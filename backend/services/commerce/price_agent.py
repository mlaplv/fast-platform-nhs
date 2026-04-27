import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

# Schema chi tiết cho từng kết quả tìm kiếm
class SearchResult(BaseModel):
    platform: str = Field(description="Nền tảng (Shopee, Lazada, Tiki, Website riêng, v.v.)")
    title: str = Field(description="Tiêu đề sản phẩm hoặc tên website")
    price: Optional[float] = Field(None, description="Giá sản phẩm nếu tìm thấy")
    link: str = Field(description="Đường dẫn đến sản phẩm hoặc website")
    is_ad: bool = Field(False, description="Đây có phải là kết quả quảng cáo/tài trợ (Sponsored/Ads) không")

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        # CẤM các định dạng link ảo thường thấy khi AI hallucinate
        fake_patterns = [
            r"i\.\d+\.\d+", 
            r"123456",       
            r"890123",       
            r"abc123",       # Cấm chuỗi abc123
            r"xyz",          # Cấm chuỗi xyz
            r"example\.com",
            r"test\.com",
            r"domain\.vn",
            r"placeholder",
            r"/tag/",
            r"/catalog/"
        ]
        
        if any(seq in v.lower() for seq in ["abc123", "xyz", "12345", "67890"]):
             raise ValueError(f"Phát hiện link ảo (chuỗi placeholder): {v}")

        for pattern in fake_patterns:
            if re.search(pattern, v):
                # Ngoại lệ: Nếu link thật sự chứa các pattern này nhưng là link sàn lớn (hiếm gặp)
                # Tuy nhiên với 12345678 thì chắc chắn là giả
                if "123456" in v or "890123" in v:
                    raise ValueError(f"Phát hiện link ảo: {v}. Yêu cầu chỉ dùng link thật từ Search Grounding.")
        
        # Link Shopee thật thường có định dạng dài và loằng ngoằng, không bao giờ là 1234567
        return v

# Schema trả về nghiêm ngặt cho Agent
class MarketPriceIntel(BaseModel):
    ads: List[SearchResult] = Field(default_factory=list, description="Danh sách các kết quả quảng cáo (Sponsored/Ads)")
    organic_results: List[SearchResult] = Field(default_factory=list, description="Top 10 kết quả tìm kiếm thông thường từ trang đầu")
    analysis: str = Field(description="Phân tích tổng quan về thị trường, xu hướng giá và lời khuyên chiến lược")

# Agent definition (Elite V2.2)
price_agent = Agent(
    output_type=MarketPriceIntel,
    system_prompt="""Bạn là chuyên gia tình báo giá và phân tích thị trường cao cấp của FAST-PLATFORM.
Nhiệm vụ: Sử dụng Search Grounding để thực hiện một cuộc trinh sát toàn diện trên internet cho sản phẩm được yêu cầu.

Yêu cầu cụ thể:
1. ADS: Lấy link SP và giá từ "Sản phẩm được tài trợ".
2. TOP 10: Lấy link SP thật và giá từ kết quả tự nhiên.
3. BIẾN THỂ: Chọn đúng giá cho phiên bản yêu cầu (ví dụ: 30g).
4. LINK: Chỉ lấy link Landing Page thật. CẤM chế link, cấm lấy link tag/search.

Lưu ý: Bạn là chuyên gia trinh sát. Phải trả về dữ liệu thật 100%. Nếu không thấy, hãy báo cáo trung thực.

Lưu ý: Nếu thấy phần "Sản phẩm được tài trợ" (Shopping carousel), BẮT BUỘC phải trích xuất vào danh sách `ads`. Đây là vùng dữ liệu ưu tiên số 1 của Sếp. CẤM tự tạo ra các dãy số như 1234567, 890123 hay chuỗi abc123xyz trong link. Link thật phải dài và phức tạp, không bao giờ ngắn gọn kiểu placeholder.
""",
)

async def scan_product_price(product_name: str) -> MarketPriceIntel:
    """Trigger AI Agent to scan market price with enhanced intelligence (Ads + Top 10 Organic)."""
    # Elite V2.2 Query Expansion: Thêm các từ khóa để kích hoạt Shopping Ads trong Search Grounding
    # Elite V2.2 Query Expansion: Trinh sát sâu theo định danh sản phẩm
    prompt = f"Phân tích thị trường và tìm link landing page chính xác cho: {product_name}. Ưu tiên các shop Mall, chính hãng và đúng biến thể. Bỏ qua mọi kết quả là trang tag hoặc tìm kiếm danh mục."

    result = await trinity_bridge.run(
        agent=price_agent,
        prompt=prompt,
        role="brain",
        safety_none=True, # Tránh việc bị chặn nhầm bởi filter an toàn khi quét web
        timeout=90.0,    # 90s là đủ để trinh sát sâu
        model_settings={
            "google_search": True,
            "google_search_retrieval": True 
        }
    )

    # TrinityBridge returns result.data directly if available
    return result
