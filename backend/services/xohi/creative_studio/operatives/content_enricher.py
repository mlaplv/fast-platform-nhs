import asyncio
import logging
import re
import os
from typing import List, Dict, Optional
from datetime import datetime

from pydantic_ai import Agent
from backend.utils.http_client import get_http_client
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.models.schemas import EnrichResponse, EnrichmentItem, EnrichAIPayload
from backend.database.repositories import ContentCampaignRepository

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
        self.search_keys = None # Lazy load
        
        if not hasattr(ContentEnricher, "_key_idx"):
            ContentEnricher._key_idx = 0
            
        self._agent = Agent(output_type=EnrichAIPayload, system_prompt=ENRICHER_PROMPT, retries=3)

    async def _emit_log(self, campaign: ContentCampaign, msg: str):
        """Emit progress event to the system bus."""
        from backend.services.event_bus import event_bus
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": str(campaign.id),
            "user_id": str(campaign.user_id),
            "message": msg,
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def _ensure_keys(self):
        if self.search_keys is not None:
            return
            
        logger.info("[Enricher] Loading search keys from environment...")
        self.search_keys = []
        # Support both underscore and non-underscore patterns for maximum compatibility
        patterns = ["", "_1", "_2", "1", "2", "3"]
        for i in patterns:
            k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
            cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx:
                self.search_keys.append({"key": k, "cx": cx})
        
        logger.info(f"[Enricher] Loaded {len(self.search_keys)} search keys.")

    async def _get_search_pair(self) -> Optional[Dict[str, str]]:
        self._ensure_keys()
        if not self.search_keys: 
            logger.warning("[Enricher] No GOOGLE_SEARCH_API_KEY found in environment (patterns: '', '_1', '1', etc.)")
            return None
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

    async def enrich(self, campaign) -> EnrichResponse:
        logs = ["🔍 Khởi động hệ thống AI Booster (Phase 82.8)..."]
        await self._emit_log(campaign, logs[-1])
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
        logs.append(f"🧠 Đang phân tích chủ đề: '{topic}'...")
        await self._emit_log(campaign, logs[-1])

        # Phase 1: Gather Real Data (Parallel)
        logs.append("📡 Đang trinh sát dữ liệu thực tế từ Google (Stats & Quotes)...")
        await self._emit_log(campaign, logs[-1])
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
        logs.append("🧠 Đang tổng hợp số liệu và chèn vào bản thảo...")
        await self._emit_log(campaign, logs[-1])
        try:
            # Use role="brain" for complex synthesis tasks
            result = await trinity_bridge.run(self._agent, user_input, role="brain")
        except Exception as ai_err:
            logger.error(f"[Enricher] AI Synthesis Fail: {ai_err}")
            logs.append(f"❌ Lỗi xử lý AI: {str(ai_err)[:100]}...")
            raise
        
        if not result or not hasattr(result, "data") or result.data is None:
            # CNS V82.50: Enhanced AI response diagnostics
            raw_text = "N/A"
            if result and hasattr(result, "all_messages"):
                # Extract text from the last message to see what went wrong
                last_msg = result.all_messages()[-1]
                raw_text = str(last_msg)
            
            logger.error(f"[Enricher] AI returned invalid data. Result: {result is not None} | Data: {getattr(result, 'data', 'N/A')}")
            logger.error(f"[Enricher] Raw Payload (first 500 chars): {raw_text[:500]}")
            raise ValueError("AI fail to generate enriched content structure")
            
            
        logger.info(f"[Enricher] Enrichment complete. Stats: {result.data.stats_added}, Quotes: {result.data.quotes_added}")
        logs.append(f"✅ Hoàn tất! Đã chèn {result.data.stats_added} số liệu, {result.data.quotes_added} câu quote và {result.data.tables_added} bảng so sánh.")
        await self._emit_log(campaign, logs[-1])
        
        # Convert EnrichAIPayload to EnrichResponse by adding logs
        return EnrichResponse(
            **result.data.model_dump(),
            logs=logs
        )

enricher = ContentEnricher()
