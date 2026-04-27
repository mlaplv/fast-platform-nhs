import logging
import asyncio
import httpx
import re
import json
import random
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, HttpUrl, JsonValue
from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.google_search import google_search_service

logger = logging.getLogger("api-gateway")

# --- 0. VN PRICE NORMALIZATION ENGINE (Layer 6) ---

# Realistic browser User-Agents for rotation (Anti-Block Layer 3)
_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

# Pre-compiled regexes for VN price extraction
_VN_PRICE_WITH_SUFFIX = re.compile(
    r'([\d]{1,3}(?:[.,]\d{3})+)\s*(?:đ|VND|VNĐ|₫)',
    re.IGNORECASE
)
_VN_PRICE_K_SUFFIX = re.compile(
    r'(\d{2,4})\s*(?:k|K|nghìn)\b',
    re.IGNORECASE
)
_VN_PRICE_TR_SUFFIX = re.compile(
    r'(\d{1,2}[.,]?\d{0,2})\s*(?:tr|triệu)\b',
    re.IGNORECASE
)
_VN_PRICE_BARE_LARGE = re.compile(
    r'(?:giá|price|:)\s*([\d]{1,3}(?:[.,]\d{3})+)',
    re.IGNORECASE
)

# Ad detection patterns (Layer 4)
_AD_LINK_PATTERNS: List[str] = [
    "googleadservices.com",
    "google.com/aclk",
    "doubleclick.net",
    "/aclk?",
]
_AD_SNIPPET_KEYWORDS: List[str] = [
    "quảng cáo", "được tài trợ", "sponsored", "ad ·",
]
_TRUSTED_ECOMMERCE: List[str] = [
    "shopee.vn", "lazada.vn", "tiki.vn", "sendo.vn",
    "hasaki.vn", "guardian.com.vn", "watsons.vn",
]


def normalize_vn_price(raw: str) -> Optional[float]:
    """
    [ELITE V3.0] Chuẩn hóa mọi format giá Việt Nam về float.
    Hỗ trợ:
      1.200.000đ → 1200000.0
      1,200,000 VND → 1200000.0
      350k → 350000.0
      1,2 triệu → 1200000.0
      490000 → 490000.0
      350.000 → 350000.0
    """
    if not raw:
        return None

    text = raw.strip()

    # Strategy 1: "k" suffix (350k → 350000)
    m_k = _VN_PRICE_K_SUFFIX.search(text)
    if m_k:
        try:
            return float(m_k.group(1)) * 1000
        except ValueError:
            pass

    # Strategy 2: "triệu/tr" suffix (1,2 triệu → 1200000)
    m_tr = _VN_PRICE_TR_SUFFIX.search(text)
    if m_tr:
        try:
            num_str = m_tr.group(1).replace(",", ".")
            return float(num_str) * 1_000_000
        except ValueError:
            pass

    # Strategy 3: Number with VND suffix (1.200.000đ, 350,000 VND)
    m_suffix = _VN_PRICE_WITH_SUFFIX.search(text)
    if m_suffix:
        return _parse_vn_number(m_suffix.group(1))

    # Strategy 4: Bare large number after price keyword
    m_bare = _VN_PRICE_BARE_LARGE.search(text)
    if m_bare:
        return _parse_vn_number(m_bare.group(1))

    # Strategy 5: Plain numeric string (e.g. from JSON-LD "price": "490000")
    clean = re.sub(r'[^\d.]', '', text)
    if clean:
        try:
            val = float(clean)
            # Sanity: VN products rarely cost < 1000 or > 100M
            if 1000 <= val <= 100_000_000:
                return val
        except ValueError:
            pass

    return None


def _parse_vn_number(num_str: str) -> Optional[float]:
    """Parse a VN-formatted number string into float.
    '1.200.000' → 1200000.0
    '1,200,000' → 1200000.0
    '350.000' → 350000.0
    """
    # Detect separator style: dots vs commas
    dot_count = num_str.count('.')
    comma_count = num_str.count(',')

    if dot_count > 0 and comma_count == 0:
        # VN-style: dots as thousands separator → remove all dots
        cleaned = num_str.replace('.', '')
    elif comma_count > 0 and dot_count == 0:
        # US-style: commas as thousands separator → remove all commas
        cleaned = num_str.replace(',', '')
    elif dot_count > 0 and comma_count > 0:
        # Mixed: assume last separator is decimal (unlikely for VN prices)
        # E.g. "1,200.50" or "1.200,50" — just strip all to digits
        cleaned = re.sub(r'[.,]', '', num_str)
    else:
        cleaned = num_str

    try:
        val = float(cleaned)
        if 1000 <= val <= 100_000_000:
            return val
    except ValueError:
        pass
    return None


def detect_is_ad(link: str, snippet: str) -> bool:
    """[ELITE V3.0] Layer 4: Heuristic ad detection from link + snippet."""
    link_lower = link.lower()
    for pattern in _AD_LINK_PATTERNS:
        if pattern in link_lower:
            return True

    snippet_lower = snippet.lower()
    for kw in _AD_SNIPPET_KEYWORDS:
        if kw in snippet_lower:
            return True

    return False


# --- 1. DATA MODELS ---

class RawSearchResult(BaseModel):
    """Elite V3.0: Dữ liệu thô từ Google Search Engine."""
    title: str
    link: HttpUrl
    snippet: str
    displayLink: Optional[str] = None
    pagemap: Dict[str, JsonValue] = Field(default_factory=dict)

    def extract_metadata_price(self) -> Optional[float]:
        """[V3.0] Multi-layer pagemap extraction + VN price normalization.

        Tầng 1: offer / offers schema (Google Shopping)
        Tầng 2: product schema
        Tầng 3: metatags (og:price:amount, product:price:amount)
        Tầng 4: hproduct microformat
        Tầng 5: Snippet regex (mở rộng)
        """
        try:
            # --- Tầng 1: offer / offers schema ---
            offers = self.pagemap.get('offer', []) or self.pagemap.get('offers', [])
            if isinstance(offers, list) and offers:
                first = offers[0]
                if isinstance(first, dict):
                    price_raw = first.get('price') or first.get('lowprice') or first.get('highprice')
                    if price_raw:
                        normalized = normalize_vn_price(str(price_raw))
                        if normalized:
                            return normalized

            # --- Tầng 2: product schema ---
            products = self.pagemap.get('product', [])
            if isinstance(products, list) and products:
                for p in products:
                    if isinstance(p, dict):
                        for key in ('price', 'lowprice', 'saleprice', 'regularprice'):
                            if key in p:
                                normalized = normalize_vn_price(str(p[key]))
                                if normalized:
                                    return normalized

            # --- Tầng 3: metatags (og:price:amount, product:price:amount) ---
            metatags = self.pagemap.get('metatags', [])
            if isinstance(metatags, list) and metatags:
                for meta in metatags:
                    if isinstance(meta, dict):
                        for meta_key in (
                            'og:price:amount', 'product:price:amount',
                            'product:price', 'price', 'og:price',
                        ):
                            val = meta.get(meta_key)
                            if val:
                                normalized = normalize_vn_price(str(val))
                                if normalized:
                                    return normalized

            # --- Tầng 4: hproduct microformat ---
            hproducts = self.pagemap.get('hproduct', [])
            if isinstance(hproducts, list) and hproducts:
                for hp in hproducts:
                    if isinstance(hp, dict):
                        price_raw = hp.get('price') or hp.get('currency_range')
                        if price_raw:
                            normalized = normalize_vn_price(str(price_raw))
                            if normalized:
                                return normalized

            # --- Tầng 5: Snippet regex (mở rộng) ---
            # Thử tìm các mẫu giá phổ biến trong snippet nếu các tầng trên thất bại
            normalized = normalize_vn_price(self.snippet)
            if normalized:
                return normalized

            # Fallback cuối cùng: Tìm chuỗi số có hậu tố đ/VND/₫ ở bất kỳ đâu trong snippet
            m = re.search(r'([\d]{1,3}(?:[.,]\d{3})+)\s*(?:đ|VND|₫)', self.snippet, re.IGNORECASE)
            if m:
                return _parse_vn_number(m.group(1))

        except Exception as e:
            logger.warning(f"[PriceAgent] Pagemap extraction error: {e}")
        return None


class SearchResult(BaseModel):
    """Elite V3.0: Kết quả thị trường đã được làm sạch."""
    platform: str = Field(description="Nền tảng bán hàng")
    title: str = Field(description="Tiêu đề sản phẩm")
    price: Optional[float] = Field(None, description="Giá sản phẩm (VND)")
    link: str = Field(description="Đường dẫn sản phẩm")
    is_ad: bool = Field(False, description="Đánh dấu quảng cáo")

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        if not v.startswith("http"): raise ValueError(f"URL không hợp lệ: {v}")
        return v


class MarketPriceIntel(BaseModel):
    """Elite V3.0: Báo cáo tình báo giá thị trường hoàn chỉnh."""
    ads: List[SearchResult] = Field(default_factory=list)
    organic_results: List[SearchResult] = Field(default_factory=list)
    analysis_overview: str = Field(min_length=150)
    critical_analysis: str = Field(min_length=150)
    optimization_strategy: str = Field(min_length=100)
    viral_hook: str = Field(min_length=50)
    avg_market_price: Optional[float] = None
    min_market_price: Optional[float] = None
    competitor_count: int = 0


class NeuralScrapeResult(BaseModel):
    """Elite V3.0: Kết quả quét sâu từ website."""
    price: Optional[float] = None
    currency: str = "VND"
    availability: str = "InStock"
    confidence_score: float = 0.0
    source_type: str = "Text"
    reason: Optional[str] = None


# --- 2. AI AGENTS ---

scraper_agent: Agent[None, NeuralScrapeResult] = Agent(
    output_type=NeuralScrapeResult,
    system_prompt="""Bạn là CHUYÊN GIA TRÍCH XUẤT GIÁ (XOHI-SCRAPER V3.0).
Nhiệm vụ: Tìm GIÁ CHÍNH XÁC CỦA TARGET PRODUCT từ dữ liệu được cung cấp.

QUY TẮC ELITE:
1. JSON-LD FIRST: Ưu tiên dữ liệu "offers.price" hoặc "Product.price" trong [STRUCTURED_DATA]. Tin cậy 0.99.
2. DATA-PRICE ATTRIBUTES: Nếu có [DATA_ATTRIBUTES] chứa data-price, data-original-price → Tin cậy 0.95.
3. MAIN CONTENT ONLY: Chỉ tin dữ liệu giá trong [MAIN_CONTENT] khi không có nguồn cấu trúc.
4. ANTI-DISTRACTION: Loại bỏ giá của sản phẩm KHÁC, giá khuyến mãi chéo, banner, quà tặng.
5. PRICE SANITY: Giá sản phẩm mỹ phẩm Nhật Bản tại VN thường từ 100.000 - 2.000.000 VND. Nếu giá ngoài khoảng này, ghi confidence thấp.
6. FORMAT VN: Giá VN dùng dấu chấm hoặc dấu phẩy làm dấu phân cách hàng nghìn. Ví dụ: 350.000 = ba trăm năm mươi nghìn đồng. KHÔNG nhầm lẫn 350.000 với 350 (ba trăm năm mươi).
7. HINT: Nếu có [PRICE_HINT] từ pagemap, dùng nó để cross-validate.
8. CONFIDENCE: JSON-LD=0.99, data-attribute=0.95, meta-tag=0.90, text-regex=0.70, not-found=0.0.
""",
)

price_agent: Agent[None, MarketPriceIntel] = Agent(
    output_type=MarketPriceIntel,
    system_prompt="""Bạn là ĐIỆP VIÊN TÌNH BÁO GIÁ (XOHI PriceIntel V3.0).
Nhiệm vụ: Phân tích thị trường Việt Nam 2026. Phản biện sắc bén.

CHỈ THỊ CỐT LÕI:
1. TUYỆT ĐỐI KHÔNG HALLUCINATE: Chỉ dùng link và giá thực từ tool get_market_results.
2. LỌC RÁC TRIỆT ĐỂ (ANTI-NOISE): Loại bỏ ngay các kết quả không liên quan (VD: tìm Serum ra Bikini, đồ lót, đồ gia dụng). Không đưa vào danh sách.
3. ƯU TIÊN GIÁ GOOGLE (DIRECT HARVESTING): Nếu một kết quả có GIÁ_META (giá lấy trực tiếp từ Google) nhưng RECON báo N/A (do lỗi quét web), hãy VẪN DÙNG GIÁ_META đó. Đây là yêu cầu tối quan trọng của Sếp để lấy giá trực tiếp từ Google.
4. PHÂN LOẠI MINH BẠCH: Phân biệt rõ QUẢNG CÁO (có chữ [QUẢNG CÁO]) vs KẾT QUẢ TỰ NHIÊN.
5. TÍNH TOÁN CHÍNH XÁC: avg_market_price và min_market_price chỉ tính từ các kết quả có giá.
6. CHIẾN LƯỢC ELITE: Phản biện sắc bén về giá, đề xuất cách micsmo.com chiến thắng đối thủ.
""",
)

# --- 3. CORE TOOLS ---

def _extract_price_from_html(html: str) -> Dict[str, object]:
    """[V3.0] Smart HTML extraction: JSON-LD + data-attributes + price-class hints."""
    result: Dict[str, object] = {
        "json_ld": [],
        "data_prices": [],
        "main_text": "",
    }

    # --- JSON-LD extraction ---
    json_ld: List[object] = []
    scripts = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    for s in scripts:
        try:
            data = json.loads(s.strip())
            if isinstance(data, list):
                json_ld.extend(data)
            else:
                json_ld.append(data)
        except (json.JSONDecodeError, ValueError):
            pass
    result["json_ld"] = json_ld

    # --- Data-attribute price extraction ---
    data_prices: List[str] = []
    data_attr_matches = re.findall(
        r'data-(?:price|original-price|product-price|sale-price|final-price)\s*=\s*["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    for dp in data_attr_matches:
        normalized = normalize_vn_price(dp)
        if normalized:
            data_prices.append(f"{normalized:,.0f}")
    result["data_prices"] = data_prices

    # --- Main text extraction (clean nav/header/footer/script/style) ---
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    content = body_match.group(1) if body_match else html
    # Remove non-content sections
    content = re.sub(
        r'<(script|style|nav|header|footer|aside|iframe)[^>]*>.*?</\1>',
        '', content, flags=re.DOTALL | re.IGNORECASE
    )
    # Strip tags but preserve spacing
    content = re.sub(r'<[^>]+>', ' ', content)
    content = re.sub(r'\s+', ' ', content).strip()
    result["main_text"] = content[:4000]

    return result


@price_agent.tool
async def get_market_results(ctx: RunContext[None], query: str) -> str:
    """XOHI Recon Engine V3.0: Trích xuất dữ liệu thị trường đa tầng + multi-query."""
    clean_query = query.strip()

    # --- Layer 1: Multi-Query Strategy (2 queries song song) ---
    query_ecommerce = f"{clean_query} mua online giá site:shopee.vn OR site:lazada.vn OR site:tiki.vn OR site:hasaki.vn"
    query_official = f"{clean_query} giá bán chính hãng 2026"

    raw_ecommerce, raw_official = await asyncio.gather(
        google_search_service.search(query_ecommerce, num=10),
        google_search_service.search(query_official, num=10),
        return_exceptions=True,
    )

    # Handle exceptions from gather
    if isinstance(raw_ecommerce, BaseException):
        logger.warning(f"[PriceAgent] Ecommerce query failed: {raw_ecommerce}")
        raw_ecommerce = []
    if isinstance(raw_official, BaseException):
        logger.warning(f"[PriceAgent] Official query failed: {raw_official}")
        raw_official = []

    # Merge & dedup by link
    seen_links: set[str] = set()
    merged_raw: List[Dict[str, object]] = []
    for item in list(raw_ecommerce) + list(raw_official):
        link = str(item.get("link", ""))
        if link and link not in seen_links:
            seen_links.add(link)
            merged_raw.append(item)

    if not merged_raw:
        return "KHÔNG TÌM THẤY DỮ LIỆU."

    # Parse into typed models
    results: List[RawSearchResult] = []
    for r in merged_raw:
        try:
            results.append(RawSearchResult.model_validate(r))
        except Exception:
            pass

    if not results:
        return "KHÔNG TÌM THẤY DỮ LIỆU HỢP LỆ."

    # --- Sort: trusted ecommerce domains first ---
    def _domain_priority(r: RawSearchResult) -> int:
        domain = (r.displayLink or "").lower()
        for i, trusted in enumerate(_TRUSTED_ECOMMERCE):
            if trusted in domain:
                return i
        return 100

    results.sort(key=_domain_priority)

    # --- Deep scan với Neural Verify ---
    async def neural_verify(r: RawSearchResult, idx: int, client: httpx.AsyncClient) -> str:
        link = str(r.link)
        is_ad = detect_is_ad(link, r.snippet)
        meta_price = r.extract_metadata_price()
        ad_tag = " [QUẢNG CÁO]" if is_ad else ""
        domain = r.displayLink or "unknown"

        # Layer 3: Deep scan top 7 (tăng từ 5)
        try:
            if idx >= 7:
                price_info = f"GIÁ_META: {meta_price:,.0f} VND" if meta_price else "GIÁ_META: N/A"
                return f"[{idx+1}]{ad_tag} {r.title}\n    DOMAIN: {domain}\n    LINK: {link}\n    {price_info}\n"

            # Layer 3: UA Rotation (Anti-Block)
            ua = random.choice(_USER_AGENTS)
            resp = await client.get(
                link, timeout=8.0, follow_redirects=True,
                headers={"User-Agent": ua, "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"}
            )
            html = resp.text

            # Smart HTML Extraction
            extracted = _extract_price_from_html(html)
            json_ld_str = json.dumps(extracted["json_ld"], ensure_ascii=False)[:2000]
            data_prices_str = ", ".join(str(d) for d in extracted["data_prices"][:5])
            main_text = str(extracted["main_text"])

            # Build prompt for scraper agent
            hint_parts: List[str] = []
            if meta_price:
                hint_parts.append(f"Pagemap: {meta_price:,.0f} VND")
            if data_prices_str:
                hint_parts.append(f"data-attr: {data_prices_str}")
            hint = " | ".join(hint_parts) if hint_parts else "Không có hint"

            data: NeuralScrapeResult = await trinity_bridge.run(
                agent=scraper_agent,
                prompt=(
                    f"TARGET: {r.title}\n"
                    f"[PRICE_HINT]: {hint}\n\n"
                    f"[STRUCTURED_DATA]: {json_ld_str}\n\n"
                    f"[DATA_ATTRIBUTES]: {data_prices_str}\n\n"
                    f"[MAIN_CONTENT]: {main_text}"
                ),
                role="fast",
                timeout=30.0,
            )

            # Determine final price: prioritize scraper AI result, fallback to meta
            final_price = data.price
            confidence = data.confidence_score
            src = data.source_type
            
            if not final_price and meta_price:
                final_price = meta_price
                confidence = 0.85  # Google-native price is highly trusted
                src = "Google_Meta"

            if final_price:
                recon = f"GIÁ: {final_price:,.0f} VND (Conf: {confidence:.2f}, Src: {src})"
            else:
                recon = "GIÁ: N/A"

            return (
                f"[{idx+1}]{ad_tag} {r.title}\n"
                f"    DOMAIN: {domain}\n"
                f"    LINK: {link}\n"
                f"    RECON: {recon}\n"
                f"    REASON: {data.reason or 'N/A'}\n"
            )
        except Exception as e:
            price_info = f"GIÁ_META: {meta_price:,.0f} VND" if meta_price else "GIÁ_META: N/A"
            return f"[{idx+1}]{ad_tag} {r.title}\n    DOMAIN: {domain}\n    LINK: {link}\n    {price_info} (scrape_error: {str(e)[:80]})\n"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        scan_reports: List[str] = []
        for i, r in enumerate(results):
            report: str = await neural_verify(r, i, client)
            scan_reports.append(report)
            # Thêm delay nhỏ để tránh spam API
            await asyncio.sleep(0.2)

    return "DỮ LIỆU TRINH SÁT THỰC TẾ (V3.0):\n" + "\n".join(scan_reports)

# --- 4. PUBLIC API ---

async def scan_product_price(product_name: str) -> MarketPriceIntel:
    """Khởi chạy chiến dịch tình báo giá thị trường V3.0."""
    prompt = f"HÃY THỰC HIỆN TRINH SÁT CHO SẢN PHẨM: {product_name}"
    return await trinity_bridge.run(agent=price_agent, prompt=prompt, role="brain", timeout=150.0)
