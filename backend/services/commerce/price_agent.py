import logging
import asyncio
import httpx
import re
import os
import json
from typing import List, Optional, Dict, Tuple, Sequence, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl
from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

from backend.services.xohi.google_search import google_search_service

# [ELITE V4.0] Structural Data Models
class RawSearchResult(BaseModel):
    title: str
    link: HttpUrl
    snippet: str
    displayLink: Optional[str] = None
    pagemap: Dict[str, Any] = Field(default_factory=dict)

    def extract_metadata_price(self) -> Optional[str]:
        """Extract price from Google's rich metadata."""
        try:
            offers = self.pagemap.get('offer', []) or self.pagemap.get('offers', [])
            if isinstance(offers, list) and offers:
                first = offers[0]
                price = first.get('price')
                currency = first.get('pricecurrency', 'VND')
                if price: return f"{float(price):,.0f} {currency}"
            
            products = self.pagemap.get('product', [])
            if isinstance(products, list) and products:
                for p in products:
                    if 'price' in p: return f"{float(p['price']):,.0f} VND"
            
            # Snippet fallback
            price_match = re.search(r'(\d{1,3}(?:[.,]\d{3})*)\s?(?:đ|VND|VNĐ|k)', self.snippet, re.IGNORECASE)
            if price_match: return f"{price_match.group(0)}"
        except Exception: pass
        return None

logger = logging.getLogger("api-gateway")

class SearchResult(BaseModel):
    platform: str = Field(description="Nền tảng (Shopee, Lazada, Tiki, Website riêng, v.v.)")
    title: str = Field(description="Tiêu đề sản phẩm hoặc tên website")
    price: Optional[float] = Field(None, description="Giá sản phẩm nếu tìm thấy")
    link: str = Field(description="Đường dẫn đến sản phẩm hoặc website")
    is_ad: bool = Field(False, description="Đây có phải là kết quả quảng cáo không")

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        if not v.startswith("http"): raise ValueError(f"Invalid URL: {v}")
        return v

class MarketPriceIntel(BaseModel):
    ads: List[SearchResult] = Field(default_factory=list)
    organic_results: List[SearchResult] = Field(default_factory=list)
    analysis_overview: str = Field(min_length=100)
    critical_analysis: str = Field(min_length=100)
    optimization_strategy: str = Field(min_length=100)
    viral_hook: str = Field(min_length=50)
    avg_market_price: Optional[float] = None
    min_market_price: Optional[float] = None
    competitor_count: int = 0

price_agent: Agent[None, MarketPriceIntel] = Agent(
    output_type=MarketPriceIntel,
    system_prompt="Bạn là ĐIỆP VIÊN TÌNH BÁO GIÁ. Ưu tiên Vietnam Only. Phân tích chi tiết.",
)

class NeuralScrapeResult(BaseModel):
    price: Optional[float] = None
    currency: str = "VND"
    availability: str = "InStock"
    confidence_score: float = Field(0.0, description="Độ tin cậy của mức giá (0.0-1.0)")
    source_type: str = Field("Text", description="Nguồn trích xuất: JSON-LD, Meta, hoặc Text")
    reason: Optional[str] = None

# [ELITE V4.0] STRUCTURAL SCRAPER AGENT
scraper_agent: Agent[None, NeuralScrapeResult] = Agent(
    output_type=NeuralScrapeResult,
    system_prompt="""Bạn là CHUYÊN GIA TRÍCH XUẤT CẤU TRÚC (Code: XOHI-SCRAPER-V4.0).
Nhiệm vụ: Tìm GIÁ CHÍNH XÁC của TARGET PRODUCT dựa trên dữ liệu cấu trúc và nội dung trang.

QUY TẮC SỐNG CÒN (STRUCTURAL PRIORITY):
1. DỮ LIỆU CẤU TRÚC (JSON-LD): Luôn ưu tiên thông tin trong mục [STRUCTURED_DATA]. Nếu tìm thấy giá sản phẩm tại đây, độ tin cậy là 0.99.
2. PHÂN VÙNG NỘI DUNG: 
   - [MAIN_CONTENT]: Chứa thông tin sản phẩm chính. Tin cậy cao.
   - [HEADER/BANNER]: Chứa quảng cáo, khuyến mãi chung. CỰC KỲ NGHI NGỜ.
3. LOẠI BỎ DISTRACTION: Nếu thấy giá (ví dụ 112k) thuộc về sản phẩm khác (Matcha, Quà tặng) hoặc nằm trong banner khuyến mãi chung, hãy bỏ qua ngay.
4. ĐỐI CHIẾU HINT: Nếu Google gợi ý giá ~600k mà bạn thấy 112k trong text, hãy kiểm tra lại JSON-LD. Nếu JSON-LD không có, và 112k nằm ở vùng Header, hãy trả về price=None.
5. CONFIDENCE SCORE: Trả về điểm tin cậy dựa trên nguồn và độ khớp ngữ nghĩa.
""",
)

@price_agent.tool
async def get_market_results(ctx: RunContext[None], query: str) -> str:
    """Elite V4.0: Structural & Semantic Recon Engine."""
    clean_query = query.strip()
    enriched_query = f"{clean_query} giá bán tại Việt Nam"
    raw_results = await google_search_service.search(enriched_query, num=10)
    
    if not raw_results: return "Không tìm thấy kết quả nào."
    results: List[RawSearchResult] = [RawSearchResult.model_validate(r) for r in raw_results]
    
    async def neural_verify(r: RawSearchResult, idx: int, client: httpx.AsyncClient) -> str:
        link = str(r.link)
        meta_price = r.extract_metadata_price()
        
        try:
            if idx >= 5: # Deep scan top 5 only
                return f"[{idx+1}] {r.title}\n    LINK: {link}\n    PRICE_META: {meta_price or 'N/A'}\n"

            resp = await client.get(link, timeout=10.0, follow_redirects=True)
            html = resp.text
            
            # [ELITE V4.0] 1. Extract JSON-LD (Dữ liệu sạch nhất)
            json_ld = []
            scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            for s in scripts:
                try:
                    data = json.loads(s.strip())
                    if isinstance(data, list): json_ld.extend(data)
                    else: json_ld.append(data)
                except: pass
            
            # [ELITE V4.0] 2. Segment Content (Tách Header/Body)
            body_match = re.search(r'<body.*?>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            body_content = body_match.group(1) if body_match else html
            
            # Clean text but keep semantic hints
            def clean(t):
                t = re.sub(r'<(script|style|nav|header|footer).*?>.*?</\1>', '', t, flags=re.DOTALL | re.IGNORECASE)
                t = re.sub(r'<[^>]+>', ' ', t)
                return re.sub(r'\s+', ' ', t).strip()[:3000]

            main_text = clean(body_content)
            
            # [ELITE V4.0] 3. Run Scraper with Structural Context
            hint = f"Google Hint: {meta_price}" if meta_price else "No hint"
            struct_data_str = json.dumps(json_ld, ensure_ascii=False)[:2000]
            
            data: NeuralScrapeResult = await trinity_bridge.run(
                agent=scraper_agent,
                prompt=f"TARGET: {r.title}\n{hint}\n\n[STRUCTURED_DATA]:\n{struct_data_str}\n\n[MAIN_CONTENT]:\n{main_text}",
                role="fast",
                timeout=30.0
            )
            
            if data.price:
                res_str = f"GIÁ THỰC (NEURAL): {data.price:,.0f} {data.currency} (Conf: {data.confidence_score}, Source: {data.source_type})"
            elif meta_price:
                res_str = f"GIÁ TRÍCH XUẤT (META): {meta_price}"
            else:
                return f"[{idx+1}] [IGNORE] {r.title}\n    LINK: {link}\n"

            return f"[{idx+1}] {r.title}\n    STATUS: LIVE\n    LINK: {link}\n    RECON: {res_str}\n    REASON: {data.reason or 'N/A'}\n"
        except Exception as e:
            return f"[{idx+1}] {r.title}\n    STATUS: ERROR ({type(e).__name__})\n    LINK: {link}\n    PRICE_META: {meta_price or 'N/A'}\n"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        tasks = [asyncio.create_task(neural_verify(r, i, client)) for i, r in enumerate(results)]
        scan_results = await asyncio.gather(*tasks)
    
    return "BÁO CÁO TRINH SÁT V4.0 (STRUCTURAL):\n" + "\n".join(scan_results)

async def scan_product_price(product_name: str) -> MarketPriceIntel:
    prompt = f"HÃY THỰC HIỆN TRINH SÁT CHO SẢN PHẨM: {product_name}"
    return await trinity_bridge.run(agent=price_agent, prompt=prompt, role="brain", timeout=150.0)
