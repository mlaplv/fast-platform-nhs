import logging
import asyncio
import httpx
import re
import json
import random
from typing import List, Optional, Dict, Tuple
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
    "miccosmo.vn", "haligroup.vn", "maihan.vn", "sieuthilamdep.com",
    "chotinhcuaboo.com", "xachtaynhat.net", "domy.vn"
]

# [V3.3] Poison keywords that indicate the price might not be the product price
_POISON_PHRASES: List[str] = [
    "voucher", "mã giảm", "tặng", "phí ship", "phí vận chuyển", 
    "tặng kèm", "quà", "ưu đãi", "hoàn tiền", "cashback", "coupon",
    "giảm thêm", "ship chỉ"
]

def is_poisoned_context(text: str, start_idx: int, end_idx: int) -> bool:
    """[V3.3] Kiểm tra xem giá tìm thấy có nằm gần từ khóa gây nhiễu không.
    """
    window_start = max(0, start_idx - 20)
    window_end = min(len(text), end_idx + 25)
    context = text[window_start:window_end].lower()
    
    for phrase in _POISON_PHRASES:
        if phrase in context:
            if phrase == "phí ship" and "miễn phí ship" in context:
                continue
            return True
    return False


def normalize_vn_price(raw: str, prefer_higher: bool = True) -> Optional[float]:
    """[ELITE V3.3] Chuẩn hóa mọi format giá Việt Nam về float + Lọc độc."""
    if not raw:
        return None

    text = raw.strip()
    valid_prices: List[float] = []

    for m in _VN_PRICE_WITH_SUFFIX.finditer(text):
        price = _parse_vn_number(m.group(1))
        if price and not is_poisoned_context(text, m.start(), m.end()):
            valid_prices.append(price)

    for m in _VN_PRICE_K_SUFFIX.finditer(text):
        price = float(m.group(1)) * 1000
        if price >= 1000 and not is_poisoned_context(text, m.start(), m.end()):
            valid_prices.append(price)

    for m in _VN_PRICE_TR_SUFFIX.finditer(text):
        try:
            num_str = m.group(1).replace(",", ".")
            price = float(num_str) * 1_000_000
            if not is_poisoned_context(text, m.start(), m.end()):
                valid_prices.append(price)
        except ValueError: pass

    for m in _VN_PRICE_BARE_LARGE.finditer(text):
        price = _parse_vn_number(m.group(1))
        if price and not is_poisoned_context(text, m.start(), m.end()):
            valid_prices.append(price)

    if valid_prices:
        sane_prices = [p for p in valid_prices if 10000 <= p <= 10_000_000]
        if sane_prices:
            return max(sane_prices) if prefer_higher else sane_prices[0]
        return max(valid_prices)

    clean = re.sub(r'[^\d.]', '', text)
    if len(clean) >= 4:
        try:
            val = float(clean)
            if 10000 <= val <= 100_000_000:
                return val
        except ValueError: pass

    return None


def _parse_vn_number(num_str: str) -> Optional[float]:
    """Parse a VN-formatted number string into float."""
    dot_count = num_str.count('.')
    comma_count = num_str.count(',')

    if dot_count > 0 and comma_count == 0:
        cleaned = num_str.replace('.', '')
    elif comma_count > 0 and dot_count == 0:
        cleaned = num_str.replace(',', '')
    elif dot_count > 0 and comma_count > 0:
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


def check_relevance(product_name: str, result_title: str) -> bool:
    """[ELITE V3.3] Heuristic relevance check."""
    p_name = product_name.lower()
    r_title = result_title.lower()
    
    brands = ["miccosmo", "white label", "hurry harry", "beppin body", "okurabito"]
    for brand in brands:
        if brand in p_name and brand in r_title:
            return True
            
    skincare_keywords = ["kem", "cream", "serum", "gel", "tẩy", "dưỡng", "body", "neck", "mặt", "face"]
    skincare_product = any(k in p_name for k in skincare_keywords)
    
    if skincare_product:
        irrelevant = ["bikini", "quần", "áo", "giày", "túi", "đồ lót"]
        if any(irr in r_title for irr in irrelevant):
            return False
            
    p_words = set(re.findall(r'\w+', p_name))
    r_words = set(re.findall(r'\w+', r_title))
    overlap = p_words.intersection(r_words)
    
    significant_overlap = [w for w in overlap if len(w) > 3]
    return len(significant_overlap) >= 1

def detect_ad_type(link: str, snippet: str, pagemap: Dict) -> Tuple[bool, Optional[str], str]:
    """[ELITE V3.4] Phân loại quảng cáo & Universal Tracking Cleanup.
    Returns: (is_ad, ad_type, cleaned_link)
    """
    is_ad = False
    ad_type = None
    link_str = str(link)
    link_lower = link_str.lower()
    snippet_lower = snippet.lower()
    
    from urllib.parse import urlparse, parse_qs, unquote, urlunparse, urlencode
    
    # 1. First, check if it's a Google Redirect (aclk)
    target_url = link_str
    if any(p in link_lower for p in _AD_LINK_PATTERNS):
        is_ad = True
        ad_type = "SEARCH_AD"
        if "adurl=" in link_str:
            try:
                parsed = urlparse(link_str)
                qs = parse_qs(parsed.query)
                if 'adurl' in qs:
                    target_url = unquote(qs['adurl'][0])
            except Exception: pass

    # 2. Universal Surgical Cleanup & Auto-Ad Detection
    cleaned_link = target_url
    try:
        u_parsed = urlparse(target_url)
        u_qs = parse_qs(u_parsed.query)
        
        # Define tracking/noise parameters
        tracking_params = ['gad', 'gclid', 'gbraid', 'wbraid', 'utm_', 'gads_t_sig', 'fbclid']
        
        # If the link HAS tracking params, it's very likely an ad (or from a campaign)
        has_tracking = any(
            any(tp in k.lower() for tp in tracking_params) 
            for k in u_qs.keys()
        )
        
        if has_tracking:
            is_ad = True
            if not ad_type: ad_type = "SHOPPING_AD" # Default for direct links with tracking

        # Filter out tracking junk
        clean_qs = {
            k: v for k, v in u_qs.items() 
            if not any(tp in k.lower() for tp in tracking_params)
        }
        
        # Reconstruct clean URL
        query_str = urlencode(clean_qs, doseq=True)
        cleaned_link = urlunparse(u_parsed._replace(query=query_str))
    except Exception: pass

    # 3. Snippet-based detection (Backup)
    if "ad ·" in snippet_lower or "sponsored ·" in snippet_lower or "được tài trợ" in snippet_lower:
        is_ad = True
        if not ad_type: ad_type = "SEARCH_AD"

    # 4. Shopping Ads detection via pagemap
    if is_ad and (pagemap.get('offer') or pagemap.get('product') or pagemap.get('shopping')):
        ad_type = "SHOPPING_AD"
            
    return is_ad, ad_type, cleaned_link


# --- 1. DATA MODELS ---

class RawSearchResult(BaseModel):
    """Elite V3.0: Dữ liệu thô từ Google Search Engine."""
    title: str
    link: HttpUrl
    snippet: str
    displayLink: Optional[str] = None
    pagemap: Dict[str, JsonValue] = Field(default_factory=dict)

    def extract_metadata_price(self) -> Optional[float]:
        """[V3.3] Ultra-Aggressive Metadata Extraction with Poison Filtering."""
        try:
            offers = self.pagemap.get('offer', []) or self.pagemap.get('offers', [])
            if isinstance(offers, list) and offers:
                for off in offers:
                    if isinstance(off, dict):
                        price_raw = off.get('price') or off.get('lowprice') or off.get('highprice')
                        if price_raw:
                            normalized = normalize_vn_price(str(price_raw))
                            if normalized: return normalized

            products = self.pagemap.get('product', [])
            if isinstance(products, list) and products:
                for p in products:
                    if isinstance(p, dict):
                        for key in ('price', 'lowprice', 'saleprice', 'regularprice'):
                            if key in p:
                                normalized = normalize_vn_price(str(p[key]))
                                if normalized: return normalized

            price_from_title = normalize_vn_price(self.title)
            if price_from_title:
                return price_from_title

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
                                if normalized: return normalized

            normalized = normalize_vn_price(self.snippet, prefer_higher=True)
            if normalized:
                return normalized

            bare_matches = re.findall(r'\b([\d]{1,3}(?:[.,]\d{3})+)\b', self.snippet)
            valid_bare = []
            for bm in bare_matches:
                p = _parse_vn_number(bm)
                if p and 150000 <= p <= 5000000: 
                    start_idx = self.snippet.find(bm)
                    if not is_poisoned_context(self.snippet, start_idx, start_idx + len(bm)):
                        valid_bare.append(p)
            
            if valid_bare:
                return max(valid_bare)

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
    ad_type: Optional[str] = Field(None, description="Loại quảng cáo: SEARCH_AD hoặc SHOPPING_AD")

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        if not v.startswith("http"): raise ValueError(f"URL không hợp lệ: {v}")
        return v


class MarketPriceIntel(BaseModel):
    """Elite V3.0: Báo cáo tình báo giá thị trường hoàn chỉnh."""
    ads: List[SearchResult] = Field(default_factory=list)
    organic_results: List[SearchResult] = Field(default_factory=list)
    analysis_overview: str = Field(min_length=50, description="Tổng quan thị trường và đánh giá giá trị sản phẩm.")
    critical_analysis: str = Field(min_length=50, description="Phản biện về giá của đối thủ và rủi ro.")
    optimization_strategy: str = Field(min_length=50, description="Chiến lược tối ưu giá để micsmo.com chiến thắng.")
    viral_hook: str = Field(min_length=30, description="Câu hook truyền thông thu hút khách hàng.")
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
4. ANTI-DISTRACTION: Loại bỏ giá của sản phẩm KHÁC, giá khuyến mãi chéo, banner, quà tặng, VOUCHER (50k, 100k), hoặc PHÍ SHIP.
5. PRICE SANITY: Giá sản phẩm mỹ phẩm Nhật Bản tại VN thường từ 100.000 - 2.000.000 VND. Nếu giá ngoài khoảng này, ghi confidence thấp.
6. FORMAT VN: Giá VN dùng dấu chấm hoặc dấu phẩy làm dấu phân cách hàng nghìn. Ví dụ: 350.000 = ba trăm năm mươi nghìn đồng. KHÔNG nhầm lẫn 350.000 với 350 (ba trăm năm mươi).
7. HINT: Nếu có [PRICE_HINT] từ pagemap, dùng nó để cross-validate.
8. CONFIDENCE: JSON-LD=0.99, data-attribute=0.95, meta-tag=0.90, text-regex=0.70, not-found=0.0.
""",
)

price_agent: Agent[None, MarketPriceIntel] = Agent(
    output_type=MarketPriceIntel,
    system_prompt="""Bạn là ĐIỆP VIÊN TÌNH BÁO GIÁ (XOHI PriceIntel V3.3).
Nhiệm vụ: Phân tích thị trường Việt Nam 2026 với độ TRUNG THỰC TUYỆT ĐỐI.

QUY TẮC TÁC CHIẾN (CẤM SAI LỆCH DỮ LIỆU):
1. TRUNG THỰC LÀ TỐI THƯỢNG: Chỉ dùng dữ liệu từ tool get_market_results. CẤM tự bịa kết quả.
2. PHÂN LOẠI CỨNG (NO HALLUCINATION):
   - Tuyệt đối KHÔNG được đưa kết quả [ORGANIC] vào mục 'ads'. Dù đó là trang chủ của hãng thì vẫn là Organic nếu tool báo vậy.
   - Chỉ đưa kết quả có tag [SEARCH_AD] hoặc [SHOPPING_AD] vào mục 'ads'.
   - Nếu tool trả về 5 kết quả Organic, bạn phải điền đúng 5 kết quả vào 'organic_results'. KHÔNG được gộp, KHÔNG được tách, KHÔNG được đổi tên tiêu đề.
3. GIÁ N/A: Nếu tool báo GIÁ: N/A, bạn phải để giá là null. KHÔNG được tự đoán giá từ snippet.
4. ANTI-POISON: Loại bỏ Voucher/Phí ship khỏi giá sản phẩm.

VÍ DỤ MẪU (DÙNG ĐỂ HỌC FORMAT, CẤM LẤY DỮ LIỆU TRONG NÀY):
--- Tool Output ---
[1] CATEGORY: ORGANIC | Miccosmo Official Site
    DOMAIN: miccosmo.vn
    LINK: https://miccosmo.vn/real-product-link
    GIÁ: 600.000 VND
[2] CATEGORY: SHOPPING_AD | Shopee - Beppin Body
    DOMAIN: shopee.vn
    LINK: https://shopee.vn/real-ad-link
    GIÁ: 540.000 VND
--- Kết quả Pydantic ---
ads: [{title: "Shopee - Beppin Body", price: 540000, is_ad: true, ad_type: "SHOPPING_AD"}]
organic_results: [{title: "Miccosmo Official Site", price: 600000, is_ad: false}]
--- GIẢI THÍCH: Cấm dùng link /xyz hay link trong ví dụ. Phải dùng Link thực tế từ tool. ---

PHÂN TÍCH CHI TIẾT:
- analysis_overview: Đánh giá dựa trên đúng số liệu thực tế.
- critical_analysis: Phản biện sắc bén về sự chênh lệch giá giữa các sàn và trang hãng.
- optimization_strategy: Chiến lược chiếm lĩnh thị trường.
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

    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    content = body_match.group(1) if body_match else html
    content = re.sub(
        r'<(script|style|nav|header|footer|aside|iframe)[^>]*>.*?</\1>',
        '', content, flags=re.DOTALL | re.IGNORECASE
    )
    content = re.sub(r'<[^>]+>', ' ', content)
    content = re.sub(r'\s+', ' ', content).strip()
    result["main_text"] = content[:4000]

    return result


@price_agent.tool
async def get_market_results(ctx: RunContext[None], query: str) -> str:
    """XOHI Recon Engine V3.0: Trích xuất dữ liệu thị trường đa tầng + multi-query."""
    clean_query = query.strip()
    search_query = f"{clean_query} giá bán"
    raw_results = await google_search_service.search(search_query, num=10)
    merged_raw = list(raw_results) if raw_results else []

    if not merged_raw:
        return "KHÔNG TÌM THẤY DỮ LIỆU."

    results: List[RawSearchResult] = []
    seen_domains: set = set()

    for r in merged_raw:
        try:
            model = RawSearchResult.model_validate(r)
            domain = (model.displayLink or "").lower()
            
            # Universal Ad & Tracking Detection
            is_ad, ad_type, unmasked_link = detect_ad_type(str(model.link), model.snippet, model.pagemap)
            
            if not is_ad:
                # [ELITE V3.5] DOMAIN DIVERSITY FILTER (Anti-Redundancy)
                if domain in seen_domains:
                    continue
                
                if not check_relevance(clean_query, model.title):
                    continue
                
                seen_domains.add(domain)
            
            results.append(model)
        except Exception:
            pass

    if not results:
        return "KHÔNG TÌM THẤY DỮ LIỆU HỢP LỆ."

    def _domain_priority(r: RawSearchResult) -> int:
        domain = (r.displayLink or "").lower()
        for i, trusted in enumerate(_TRUSTED_ECOMMERCE):
            if trusted in domain:
                return i
        return 100

    results.sort(key=_domain_priority)

    async def neural_verify(r: RawSearchResult, idx: int, client: httpx.AsyncClient) -> str:
        link = str(r.link)
        is_ad, ad_type, unmasked_link = detect_ad_type(link, r.snippet, r.pagemap)
        meta_price = r.extract_metadata_price()
        domain = r.displayLink or "unknown"
        
        if is_ad:
            # [ELITE V3.3] ADS ALWAYS BYPASS DEEP SCRAPE. 
            price_info = f"GIÁ: {meta_price:,.0f} VND (Source: Google_Ads)" if meta_price else "GIÁ: N/A"
            return f"[{idx+1}] CATEGORY: {ad_type} | {r.title}\n    DOMAIN: {domain}\n    LINK: {unmasked_link}\n    {price_info}\n"

        category = "CATEGORY: ORGANIC"
        if meta_price:
            return f"[{idx+1}] {category} | {r.title}\n    DOMAIN: {domain}\n    LINK: {link}\n    GIÁ: {meta_price:,.0f} VND (Source: Google_Extract)\n"

        if idx >= 5:
            return f"[{idx+1}] {category} | {r.title}\n    DOMAIN: {domain}\n    LINK: {link}\n    GIÁ: N/A\n"

        try:
            ua = random.choice(_USER_AGENTS)
            resp = await client.get(
                link, timeout=8.0, follow_redirects=True,
                headers={"User-Agent": ua, "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"}
            )
            html = resp.text
            extracted = _extract_price_from_html(html)
            json_ld_str = json.dumps(extracted["json_ld"], ensure_ascii=False)[:2000]
            data_prices_str = ", ".join(str(d) for d in extracted["data_prices"][:5])
            main_text = str(extracted["main_text"])

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

            final_price = data.price
            confidence = data.confidence_score
            src = data.source_type
            
            if not final_price and meta_price:
                final_price = meta_price
                confidence = 0.85
                src = "Google_Meta"

            if final_price:
                recon = f"GIÁ: {final_price:,.0f} VND (Conf: {confidence:.2f}, Src: {src})"
            else:
                recon = "GIÁ: N/A"

            return (
                f"[{idx+1}] {category} | {r.title}\n"
                f"    DOMAIN: {domain}\n"
                f"    LINK: {link}\n"
                f"    RECON: {recon}\n"
                f"    REASON: {data.reason or 'N/A'}\n"
            )
        except Exception as e:
            price_info = f"GIÁ_META: {meta_price:,.0f} VND" if meta_price else "GIÁ_META: N/A"
            return f"[{idx+1}] {category} | {r.title}\n    DOMAIN: {domain}\n    LINK: {link}\n    {price_info} (scrape_error: {str(e)[:80]})\n"

    sem = asyncio.Semaphore(2)
    async def limited_verify(r, i, cl):
        async with sem:
            return await neural_verify(r, i, cl)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [limited_verify(r, i, client) for i, r in enumerate(results)]
        scan_reports = await asyncio.gather(*tasks)

    valid_prices = [r.extract_metadata_price() for r in results if r.extract_metadata_price()]
    avg_p = sum(valid_prices) / len(valid_prices) if valid_prices else 0
    min_p = min(valid_prices) if valid_prices else 0
    
    return f"DỮ LIỆU TRINH SÁT THỰC TẾ (V3.0):\n" + "\n".join(scan_reports) + f"\n\n[HEURISTIC_STATS]: avg={avg_p}, min={min_p}, count={len(valid_prices)}"


# --- 4. PUBLIC API ---

async def scan_product_price(product_name: str) -> MarketPriceIntel:
    """Khởi chạy chiến dịch tình báo giá thị trường V3.0 (Elite V2.2: Heuristic Fallback)."""
    prompt = f"HÃY THỰC HIỆN TRINH SÁT CHO SẢN PHẨM: {product_name}"
    
    try:
        return await trinity_bridge.run(agent=price_agent, prompt=prompt, role="brain", timeout=120.0)
    except Exception as e:
        logger.warning(f"⚠️ [PriceAgent] Neural Engine bận ({str(e)[:50]}). Kích hoạt Heuristic Mode...")
        
        raw_results = await google_search_service.search(f"{product_name} giá bán", num=10)
        
        prices = []
        organic = []
        ads = []
        seen_domains: set = set()

        for r in raw_results:
            try:
                res = RawSearchResult.model_validate(r)
                p = res.extract_metadata_price()
                link = str(res.link)
                domain = (res.displayLink or "").lower()
                
                is_ad, ad_type, cleaned_link = detect_ad_type(link, res.snippet, res.pagemap)
                
                sr = SearchResult(
                    platform=res.displayLink or "Unknown",
                    title=res.title,
                    price=p,
                    link=cleaned_link,
                    is_ad=is_ad,
                    ad_type=ad_type
                )
                
                if is_ad: 
                    ads.append(sr)
                    continue
                
                # [ELITE V3.5] DOMAIN DIVERSITY FILTER (Heuristic Mode)
                if domain in seen_domains:
                    continue
                
                if not check_relevance(product_name, res.title):
                    continue
                
                seen_domains.add(domain)
                organic.append(sr)
                if p: prices.append(p)
            except Exception as e:
                logger.warning(f"Heuristic error for {r.get('link')}: {e}")
                continue
            
        avg_m = sum(prices) / len(prices) if prices else 0
        min_m = min(prices) if prices else 0
        
        return MarketPriceIntel(
            ads=ads,
            organic_results=organic,
            analysis_overview=f"Hệ thống đang ở chế độ Heuristic do AI quá tải. Dựa trên {len(organic)} kết quả thực tế, giá trung bình thị trường khoảng {avg_m:,.0f} VND.",
            critical_analysis=f"Phân tích cục bộ: Giá thấp nhất tìm thấy là {min_m:,.0f} VND. Đối thủ đang cạnh tranh gay gắt về giá trong phân khúc này.",
            optimization_strategy="Đề xuất: Duy trì mức giá hiện tại và tập trung vào dịch vụ hậu mãi trong khi chờ hệ thống Neural Core ổn định trở lại.",
            viral_hook="Giá tốt nhất thị trường - Kiểm chứng bởi XoHi Heuristic Engine!",
            avg_market_price=avg_m,
            min_market_price=min_m,
            competitor_count=len(prices)
        )
