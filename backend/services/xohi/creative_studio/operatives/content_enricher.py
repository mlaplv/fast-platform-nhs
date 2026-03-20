import asyncio
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

from pydantic_ai import Agent
from backend.utils.http_client import get_http_client
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.models.schemas import EnrichResponse, EnrichmentItem
from backend.database.repositories import ContentCampaignRepository
from backend.core.config import settings

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Viral Edge™ Content Enricher 
# ══════════════════════════════════════════════════════════════

ENRICHER_PROMPT = """[ROLE] VIETNAMESE SENIOR CONTENT ENRICHER (VIRAL EDGE™ 2026)
Nhiệm vụ: Nâng cấp bài viết bằng cách chèn Data Thật (Stats), Ý kiến chuyên gia (Quotes), và Bảng so sánh (Tables).

[NGUYÊN TẮC HOẠT ĐỘNG]
1. Đọc bài viết gốc (DRAFT).
2. XEM XÉT dữ liệu thực tế (DATA) được cung cấp.
3. Chèn 2-3 số liệu thống kê (phải có citation rõ ràng) vào các đoạn liên quan.
4. Chèn 1-2 câu quote của chuyên gia/authority vào bài.
5. Tạo 1 BẢNG SO SÁNH (Table) tóm tắt các khía cạnh quan trọng (nếu phù hợp).
6. TRẢ VỀ toàn bộ bài viết ĐÃ ĐƯỢC CHÈN THÊM HTML.

[QUY TẮC HTML KHI CHÈN]
- STATS: Dùng `<blockquote class="xohi-stat">📊 [Nội dung số liệu] <cite>[Nguồn]</cite></blockquote>`
- QUOTES: Dùng `<blockquote class="xohi-quote">💬 "[Trích dẫn]" — <strong>[Tên chuyên gia/Nguồn]</strong></blockquote>`
- TABLE: Dùng `<table class="xohi-compare border-collapse w-full"><thead>...</thead><tbody>...</tbody></table>`

[YÊU CẦU ĐẦU RA - JSON]
{
  "new_content": "<Toàn bộ HTML bài viết ĐÃ được chèn thêm nội dung mới (không xóa nội dung cũ, chỉ thêm vào)>",
  "items": [
    {
      "type": "<stat|quote|table>",
      "location": "<Mô tả ngắn vị trí chèn, vd: Dưới H2 'Lợi ích'>",
      "content": "<Nội dung HTML cụ thể đã chèn>"
    }
  ],
  "stats_added": <int>,
  "quotes_added": <int>,
  "tables_added": <int>,
  "seo_boost_estimate": <int khoảng 5-15 điểm>
}
"""

class ContentEnricher:
    """
    Auto-enriches articles with real stats, quotes, and comparison tables.
    Pushes SEO scores from 85 to 95+.
    """
    
    def __init__(self):
        self._key_lock = asyncio.Lock()
        
        # Parse Google Search keys
        raw_keys = settings.GOOGLE_SEARCH_KEYS or ""
        self.search_keys = []
        for pair in raw_keys.split(","):
            if "|" in pair:
                parts = pair.split("|", 1)
                self.search_keys.append({"key": parts[0].strip(), "cx": parts[1].strip()})
        
        if not hasattr(ContentEnricher, "_key_idx"):
            ContentEnricher._key_idx = 0
            
        self._agent = Agent(output_type=EnrichResponse, system_prompt=ENRICHER_PROMPT, retries=3)

    async def _get_search_pair(self) -> Optional[Dict[str, str]]:
        if not self.search_keys: return None
        async with self._key_lock:
            pair = self.search_keys[self.__class__._key_idx % len(self.search_keys)]
            self.__class__._key_idx += 1
        return pair

    async def _search_data(self, query: str) -> List[str]:
        """Fetch search snippets for a query related to the topic."""
        pair = await self._get_search_pair()
        if not pair: return []
        try:
            client = await get_http_client()
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": pair["key"],
                    "cx": pair["cx"],
                    "q": query,
                    "num": 4
                }
            )
            data = response.json()
            items = data.get("items", [])
            return [f"{item['title']}: {item.get('snippet', '')} (Nguồn: {item.get('displayLink', 'Google')})" for item in items]
        except Exception as e:
            logger.error(f"[Enricher] Search API error: {e}")
            return []

    async def enrich(self, campaign: ContentCampaignRepository) -> EnrichResponse:
        draft = campaign.draft_content or ""
        if not draft:
            raise ValueError("Không có nội dung để enrich")

        topic = campaign.get_gold_val("topic")
        if not topic:
            # Fallback to H1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', draft, re.IGNORECASE | re.DOTALL)
            if h1_match:
                topic = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            else:
                topic = "Kiến thức chung"
                
        logger.info(f"[Enricher] Starting enrichment for topic: {topic}")

        # Phase 1: Gather Real Data (Parallel)
        year = datetime.now().year
        stats_query = f"{topic} statistics {year} số liệu thống kê"
        quotes_query = f"{topic} expert quotes ý kiến chuyên gia"
        
        stats_task = asyncio.create_task(self._search_data(stats_query))
        quotes_task = asyncio.create_task(self._search_data(quotes_query))
        
        stats_results, quotes_results = await asyncio.gather(stats_task, quotes_task)
        
        data_str = "--- SỐ LIỆU TỪ GOOGLE ---\n"
        data_str += "\n".join(stats_results) if stats_results else "(Không tìm thấy số liệu mới)"
        data_str += "\n\n--- Ý KIẾN CHUYÊN GIA TỪ GOOGLE ---\n"
        data_str += "\n".join(quotes_results) if quotes_results else "(Không tìm thấy expert quote)"

        # Phase 2: Synthesis & Injection via Agent
        user_input = f"""
[BÀI VIẾT GỐC]
{draft[:12000]}

[DỮ LIỆU THỰC TẾ ĐỂ CHÈN VÀO BÀI]
{data_str}

Hãy chọn số liệu/quote hay nhất từ DỮ LIỆU THỰC TẾ và TỰ TẠO 1 bảng so sánh liên quan đến topic '{topic}', sau đó chèn khéo léo vào bài viết gốc.
TRẢ VỀ toàn bộ HTML của bài viết SAU KHI ĐÃ CHÈN.
"""
        logger.info("[Enricher] Sending to Gemini for synthesis...")
        result = await trinity_bridge.run(self._agent, user_input, model="gemini-2.5-flash")
        
        if not result or getattr(result, "data", None) is None:
            raise ValueError("AI fail to generate enriched content")
            
        logger.info(f"[Enricher] Enrichment complete. Stats: {result.data.stats_added}, Quotes: {result.data.quotes_added}")
        return result.data

enricher = ContentEnricher()
