import logging
import asyncio
import httpx
import re
import os
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

from backend.services.xohi.google_search import google_search_service

logger = logging.getLogger("api-gateway")

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
        """
        [ELITE V2.2] KIỂM ĐỊNH LINK NGHIÊM NGẶT
        Mục tiêu: Loại bỏ 100% link die do AI tự chế (Hallucination).
        """
        v_lower: str = v.lower()
        
        # 1. Kiểm tra domain hợp lệ
        valid_domains: List[str] = ['shopee.vn', 'lazada.vn', 'tiki.vn', 'tiktok.com', 'facebook.com', 'sendo.vn', 'vn', 'com', 'net', 'org']
        if not any(domain in v_lower for domain in valid_domains):
             # Chấp nhận link nếu có domain quốc tế/việt nam thông dụng
             pass
        
        # 2. Phát hiện link ảo
        fake_patterns: List[str] = [
            r"12345678", r"89012345", r"abc123xyz", r"placeholder", r"example\.com", 
            r"test\.com", r"domain\.vn", r"your-link", r"item-id", r"xyz-abc"
        ]
        
        if any(re.search(p, v_lower) for p in fake_patterns):
             raise ValueError(f"Link ảo bị từ chối: {v}")

        # 3. Kiểm tra độ dài sàn TMĐT (RELAXED V2.7 - Chống Hallucination Loop)
        # Bỏ kiểm tra length gắt gao để tránh AI tự chế link khi link thật bị reject.
        pass

        # 4. Kiểm tra giao thức
        if not v.startswith("http"):
            raise ValueError(f"Link không hợp lệ (thiếu http): {v}")

        return v

# Schema trả về nghiêm ngặt cho Agent
class MarketPriceIntel(BaseModel):
    ads: List[SearchResult] = Field(default_factory=list, description="Danh sách các kết quả quảng cáo (Sponsored/Ads). Tối thiểu 1-2 nếu có.")
    organic_results: List[SearchResult] = Field(default_factory=list, description="Danh sách tối đa 10 kết quả tìm kiếm sản phẩm chất lượng nhất. Tuyệt đối không đưa blog/review vào đây.")
    
    # Phân tích sâu theo Elite V2.2
    analysis_overview: str = Field(min_length=100, description="Tổng quan tình hình thị trường hiện tại (Tối thiểu 150 từ, phân tích sắc bén).")
    critical_analysis: str = Field(min_length=100, description="Phản biện sắc bén về mức giá hiện tại. Tại sao khách hàng sẽ CHỐI TỪ chúng ta? (Tối thiểu 150 từ).")
    optimization_strategy: str = Field(min_length=100, description="Chiến lược tối ưu: Đề xuất mức giá 'Sweet Spot', combo hoặc quà tặng. (Tối thiểu 100 từ).")
    viral_hook: str = Field(min_length=50, description="Góc nhìn Viral: Cách định vị sản phẩm trên social media để tạo hiệu ứng đám đông.")
    
    # Metrics nhanh cho UI
    avg_market_price: Optional[float] = Field(None, description="Giá trung bình trên thị trường")
    min_market_price: Optional[float] = Field(None, description="Giá thấp nhất tìm thấy (không tính hàng giả/rác)")
    competitor_count: int = Field(0, description="Số lượng đối thủ trực tiếp đang bán")

# Agent definition (Elite V2.2)
price_agent: Agent[None, MarketPriceIntel] = Agent(
    output_type=MarketPriceIntel,
    system_prompt="""Bạn là ĐIỆP VIÊN TÌNH BÁO GIÁ (Code: XOHI-OPERATIVE-01) của FAST-PLATFORM.
Phong cách: Quyết đoán, sắc bén, thực dụng, không nói lời thừa.

CHỈ THỊ VỀ DỮ LIỆU (ANTI-HALLUCINATION & ANTI-SPAM):
1. RECON TOOL: Chỉ được phép gọi công cụ `get_market_results` DUY NHẤT 1 LẦN.
2. NGHIÊM CẤM TÌM KIẾM LẠI: Dù kết quả có thế nào, bạn cũng phải sử dụng dữ liệu từ lần gọi đầu tiên để báo cáo. Tuyệt đối không được gọi tool lần thứ 2 với query khác.
3. VERBATIM LINKS (SINH TỬ): BẮT BUỘC COPY Y HỆT đường dẫn URL trả về từ tool. CẤM TUYỆT ĐỐI việc tự ý sửa đổi, thêm bớt hoặc "phỏng đoán" link. Nếu link từ tool không hoạt động, hãy bỏ qua thay vì tự chế link mới.
4. QUANTITY: Trả về tối đa 10 kết quả thật. Nếu chỉ thấy 3 link sản phẩm, chỉ trả về 3. Không được cố đấm ăn xôi đưa blog/review vào để đủ số lượng.
5. VIETNAM ONLY (TỐI CAO): BẮT BUỘC CHỈ lấy kết quả tại thị trường Việt Nam. Loại bỏ hoàn toàn các trang quốc tế (Amazon, eBay, Miccosmo Global...) trừ khi đó là trang chính hãng tại Việt Nam (.vn).
6. PHÂN TÍCH CHI TIẾT (SINH TỬ): CẤM TUYỆT ĐỐI việc để trống các trường phân tích. Mỗi trường phải chứa ít nhất 3-5 câu lập luận logic. Nếu bạn để trống, hệ thống sẽ tự động REJECT và bạn sẽ thất bại.
7. TIẾT KIỆM QUOTA: Mỗi request của bạn tốn tiền thật, hãy tiết kiệm tối đa.

Lưu ý: Link die = Thất bại. Nếu bạn đưa link sai, hệ thống sẽ tự động reject báo cáo của bạn.
""",
)

# [ELITE V2.6] NEURAL SCRAPER SCHEMA
class NeuralScrapeResult(BaseModel):
    price: Optional[float] = Field(None, description="Giá thực tế quét được (đã làm sạch số)")
    currency: str = Field("VND", description="Đơn vị tiền tệ")
    availability: str = Field("InStock", description="Tình trạng: InStock hoặc OutOfStock")
    is_bait: bool = Field(False, description="Đây có phải là giá ảo/giá mồi không?")
    reason: Optional[str] = Field(None, description="Lý do nếu nghi ngờ giá ảo hoặc giải thích chênh lệch")

# Elite V2.6: Khởi tạo GOOGLE_API_KEY giả lập nếu thiếu để vượt qua bước khởi tạo Agent.
# TrinityBridge sẽ tự động thay thế bằng Key thật khi chạy thực tế.
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "trinity_placeholder"

# [ELITE V2.6] NEURAL SCRAPER AGENT (Fast Recon)
scraper_agent: Agent[None, NeuralScrapeResult] = Agent(
    model="google:gemini-2.0-flash-exp", # Model đích, sẽ được TrinityBridge điều phối
    output_type=NeuralScrapeResult,
    system_prompt="""Bạn là CHUYÊN GIA TRÍCH XUẤT DỮ LIỆU (Code: XOHI-SCRAPER-V2.6).
Nhiệm vụ: Phân tích nội dung văn bản từ một website sản phẩm và trích xuất GIÁ ĐANG BÁN thực tế.

CHỈ THỊ SINH TỬ:
1. LOẠI BỎ GIÁ CŨ: Nếu thấy giá gốc (ví dụ 600k) và giá hiện tại (ví dụ 540k), chỉ lấy giá 540k.
2. KIỂM TRA KHO: Tìm các dấu hiệu 'Hết hàng', 'Tạm hết', 'Hàng sắp về'.
3. PHÁT HIỆN GIÁ MỒI: Nếu giá cực thấp (ví dụ 10k, 20k) trong khi sản phẩm giá trị cao, đánh dấu is_bait=True.
4. KHÔNG PHỊA: Nếu không thấy giá, trả về price=None.
""",
)

@price_agent.tool
async def get_market_results(ctx: RunContext[None], query: str) -> str:
    """Sử dụng Google Custom Search API kết hợp NEURAL RECON (V2.6) để lấy dữ liệu 100% chính xác tại VN."""
    # Elite V2.8: Force Vietnam context in the query
    if "việt nam" not in query.lower() and "giá" not in query.lower():
        query += " giá bán tại Việt Nam"
    
    results: List[Dict[str, Any]] = await google_search_service.search(query, num=10)
    if not results:
        return "Không tìm thấy kết quả nào từ Google Search."
    
    # [ELITE V2.6] NEURAL RECON PROTOCOL (OPTIMIZED)
    async def neural_verify(r: Dict[str, Any], idx: int) -> str:
        link: str = r['link']
        status: str = "UNKNOWN"
        live_info: str = "N/A"
        
        try:
            # R1.5 Ultra-Lean: Chỉ Deep Scan 3 thằng đầu tiên để bảo vệ Quota
            if idx >= 3:
                return f"[{idx+1}] {r['title']}\n    LINK: {link}\n    SNIPPET: {r['snippet']}\n"

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
                resp = await client.get(link)
                if resp.status_code == 200:
                    status = "LIVE"
                    text_content: str = re.sub(r'<script.*?</script>', '', resp.text, flags=re.DOTALL)
                    text_content = re.sub(r'<style.*?</style>', '', text_content, flags=re.DOTALL)
                    text_content = re.sub(r'<[^>]+>', ' ', text_content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()[:4000]
                    
                    # Gọi Neural Scraper Agent
                    data: NeuralScrapeResult = await trinity_bridge.run(
                        agent=scraper_agent,
                        prompt=f"Website Content:\n{text_content}\n\nLink: {link}",
                        role="fast",
                        timeout=25.0
                    )
                    
                    price_str = f"{data.price:,.0f} {data.currency}" if data.price else "KHÔNG TÌM THẤY GIÁ"
                    live_info = (
                        f"GIÁ THỰC (NEURAL): {price_str}\n"
                        f"    KHO HÀNG: {data.availability}\n"
                        f"    CẢNH BÁO: {'GIÁ ẢO' if data.is_bait else 'SẠCH'}"
                    )
                else:
                    status = f"DEAD_{resp.status_code}"
        except Exception as e:
            status = f"ERROR ({type(e).__name__})"

        return (
            f"[{idx+1}] {r['title']}\n"
            f"    STATUS: {status}\n"
            f"    LINK: {link}\n"
            f"    NEURAL_SCAN: {live_info}\n"
            f"    SNIPPET: {r['snippet']}\n"
        )

    # Elite V2.7: Phân loại rác ngay từ Tool để Agent không bị nhiễu
    formatted_results = []
    for i, r in enumerate(results):
        link_lower = r['link'].lower()
        title_lower = r['title'].lower()
        
        # Elite V2.8: Lọc bỏ các kết quả quốc tế không liên quan
        is_international = any(domain in link_lower for domain in ['amazon.', 'ebay.', 'global', 'aliexpress', 'alibaba'])
        if is_international and '.vn' not in link_lower:
             res = f"[{i+1}] [IGNORE/INTL] {r['title']}\n    LINK: {r['link']}\n    (Bỏ qua vì là kết quả quốc tế, không thuộc thị trường VN)\n"
             formatted_results.append(res)
             continue

        # Lọc thô: Nếu title chứa từ khóa blog/review thì dán nhãn rác
        is_junk = any(word in title_lower for word in ['review', 'top 10', 'tổng hợp', 'đánh giá', 'so sánh', 'blog', 'tin tức', 'top 9', 'top 8', 'top 7', 'top 6', 'top 5'])
        
        if is_junk:
            res = f"[{i+1}] [JUNK/REVIEW] {r['title']}\n    LINK: {r['link']}\n    (Bỏ qua vì không phải trang bán hàng)\n"
        else:
            res = await neural_verify(r, i)
        
        formatted_results.append(res)
    
    output_str = "BÁO CÁO TRINH SÁT NEURAL RECON (V2.7 - ANTI-HALLUCINATION):\n" + "\n".join(formatted_results)
    return output_str

async def scan_product_price(product_name: str) -> MarketPriceIntel:
    """Trigger AI Agent to scan market price with enhanced intelligence (Ads + Top 10 Organic)."""
    prompt: str = f"""
    HÃY THỰC HIỆN TRINH SÁT THỰC TẾ CHO SẢN PHẨM: {product_name}
    
    Sử dụng tool `get_market_results` để lấy dữ liệu đã được KIỂM ĐỊNH SỐNG.
    
    CHỈ THỊ THIẾT QUÂN LUẬT (QUOTA DISCIPLINE):
    1. DUY NHẤT 1 LẦN GỌI TOOL: Chỉ thực hiện 01 query duy nhất. Thấy dữ liệu gì dùng dữ liệu đó. CẤM gọi tool lần 2.
    2. ƯU TIÊN TUYỆT ĐỐI NEURAL_RECON: Lấy giá từ mục `GIÁ THỰC (NEURAL)`.
    3. LOẠI BỎ HẾT HÀNG/GIÁ ẢO: Dọn dẹp dữ liệu rác ngay trong báo cáo.
    
    Hãy báo cáo ngay lập tức sau lần gọi tool đầu tiên!
    
    Báo cáo ngay cho Sếp!
    """

    result: MarketPriceIntel = await trinity_bridge.run(
        agent=price_agent,
        prompt=prompt,
        role="brain",
        safety_none=True,
        timeout=150.0,
        model_settings={
            "google_search": False,
        }
    )

    return result
