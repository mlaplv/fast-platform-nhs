import asyncio
import logging
import re
import os
from typing import List, Dict, Optional, Type, cast
from datetime import datetime, timezone

from pydantic import BaseModel
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.utils.http_client import get_http_client
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, SearchKeyMixin, XoHiProgressMixin
from backend.services.xohi.creative_studio.models.schemas import (
    EnrichAIPayload, EnrichmentItem, EnrichResponse, SeoAnnotation
)
from backend.database.repositories import ContentCampaignRepository
from backend.utils.text import extract_readable_text
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# ELITE V2.2 CONSTANTS — AI Booster Logic
# ══════════════════════════════════════════════════════════════
MAX_ENRICH_INPUT_CHARS = 12000
ENRICH_SEARCH_COUNT = 4
MAX_LOG_ERROR_LEN = 100
MAX_PROGRESS_FAIL_LEN = 50
MAX_HISTORY_TRACE_CHARS = 500
EXPECTED_SEO_BOOST = 10

class EnrichTaskRequest(BaseModel):
    """Worker task payload for ContentEnricher."""
    campaign_id: str

class ContentEnricher(BaseAgentOperative, SearchKeyMixin, XoHiProgressMixin):
    """
    Auto-enriches articles with real stats, quotes, and comparison tables.
    Elite V2.2: Context-Aware with Neural Prompt Orchestration (NPO).
    """
    agent_id_class = "content_enricher"
    
    def __init__(self):
        super().__init__(agent_id="content_enricher")
        self._agent = Agent(output_type=EnrichAIPayload, retries=3)

    async def chat(self, request: object, **kwargs: object) -> object:
        """Standardized Heritage Entry (V2.2). Maps to self.enrich."""
        from backend.database.models import ContentCampaign
        if isinstance(request, ContentCampaign):
            return await self.enrich(request)
        # Fallback for generic calls (duck typing)
        return await self.enrich(cast(ContentCampaign, request))

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return EnrichTaskRequest

    async def process_brain_logic(self, request: EnrichTaskRequest, db: AsyncSession) -> EnrichResponse:
        repo = ContentCampaignRepository(session=db)
        campaign = await repo.get(request.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {request.campaign_id} not found")

        result = await self.enrich(campaign)
        
        # Enrich changes draft_content
        if result.new_content and result.new_content != campaign.draft_content:
            campaign.draft_content = result.new_content
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(campaign, "draft_content")
            await repo.update(campaign)
            
        return result

    async def _search_data(self, query: str) -> list[str]:
        """Fetch search snippets for a query related to the topic."""
        self._ensure_search_keys()
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
                    "num": ENRICH_SEARCH_COUNT
                }
            )
            data = response.json()
            items = data.get("items", [])
            return [f"{item['title']}: {item.get('snippet', '')} (Nguồn: {item.get('displayLink', 'Google')})" for item in items]
        except Exception as e:
            self.logger.error(f"[Enricher] Search API error: {e}")
            return []

    async def enrich(self, campaign: ContentCampaign) -> EnrichResponse:
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        self.current_step = 0
        logs = [f"🚀 [{now_str}] Khởi động hệ thống AI Booster (Phase 82.8)..."]
        await self._emit_progress(campaign, logs[-1])
        logger.warning(f"🚀 [ContentEnricher] Initializing [ENRICH] Phase 0: Data Collection...")
        draft = extract_readable_text(campaign.draft_content or "")
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
        logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Đang phân tích chủ đề: '{topic}'...")
        await self._emit_progress(campaign, logs[-1])
        self.current_step = 1
        logger.warning(f"🧠 [ContentEnricher] Phase 1: Competitor Insight Analysis...")

        # Phase 1: Gather Real Data (Parallel)
        logs.append(f"📡 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Đang trinh sát dữ liệu thực tế từ Google (Stats & Quotes)...")
        await self._emit_progress(campaign, logs[-1])
        self.current_step = 2
        logger.warning(f"📡 [ContentEnricher] Phase 2: Expert Quotes Acquisition...")
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
{draft[:MAX_ENRICH_INPUT_CHARS]}

[DỮ LIỆU THỰC TẾ ĐỂ CHÈN VÀO BÀI]
{data_str}

Hãy chọn số liệu/quote hay nhất từ DỮ LIỆU THỰC TẾ và TỰ TẠO 1 bảng so sánh liên quan đến topic '{topic}', sau đó chèn khéo léo vào bài viết gốc.
    TRẢ VỀ toàn bộ HTML của bài viết SAU KHI ĐÃ CHÈN và thống kê danh sách các mục đã chèn vào trường 'items'.
    
    [YÊU CẦU CẤU TRÚC]
    Bạn PHẢI trả về một object có cấu trúc:
    - new_content: Toàn bộ HTML bài viết (đã chèn).
    - items: Danh sách {{"type": "stat|quote|table", "location": "...", "content": "..."}} (Dùng 'content' chính xác như đã chèn để frontend highlight).
    - stats_added: Số lượng số liệu đã chèn.
    - quotes_added: Số lượng quote đã chèn.
    - tables_added: Số lượng bảng đã chèn.
    - seo_boost_estimate: Ước tính điểm SEO tăng thêm (ví dụ {EXPECTED_SEO_BOOST}).
"""
        logger.info(f"[Enricher] Enrichment complete. Stats search found {len(stats_results)} results, Quotes search found {len(quotes_results)} results.")
        logger.info(f"[Enricher] Sending to Gemini for synthesis (Payload length: {len(user_input)})...")
        logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Đang tổng hợp số liệu và chèn vào bản thảo...")
        await self._emit_progress(campaign, logs[-1])
        self.current_step = 3
        logger.warning(f"🧠 [ContentEnricher] Phase 3: Feature Comparison Synthesis...")
        try:
            shield = shield_service.get_shield_component(seed=campaign.id)
            composer.register_component(shield)
            
            # ELITE V2.2: Use extra_components to maintain thread-safety
            system_prompt = composer.compose("booster_enrich", extra_components=[shield.id])
            
            logs.append(f"📡 [CONNECT] Kết nối Neural Bridge (Role: BRAIN)...")
            await self._emit_progress(campaign, logs[-1])

            # Use role="brain" for complex synthesis tasks
            result = await self.bridge.run(self._agent, user_input, system_prompt=system_prompt, role="brain")
        except Exception as ai_err:
            self.logger.error(f"[Enricher] AI Synthesis Fail: {ai_err}")
            logs.append(f"❌ Lỗi xử lý AI: {str(ai_err)[:MAX_LOG_ERROR_LEN]}...")
            await self._emit_progress(campaign, f"❌ Lỗi AI: {str(ai_err)[:MAX_PROGRESS_FAIL_LEN]}", status="FAILED")
            raise
        
        if not result or not hasattr(result, "data") or result.data is None:
            # CNS V82.85: Trigger Fallback Extraction logic
            logger.warning("[Enricher] result.data is None. Attempting fallback extraction from message history...")
            fallback_data = self._fallback_extract(result)
            if fallback_data:
                logger.info("[Enricher] Fallback extraction successful!")
                result_data = fallback_data
            else:
                raw_text = "N/A"
                history = ""
                if result:
                    try:
                        msgs = result.all_messages()
                        raw_text = str(msgs[-1])
                        history = "\n".join([f"[{type(m).__name__}] {str(m)[:200]}..." for m in msgs])
                    except: pass
                    
                logger.error(f"[Enricher] AI returned invalid data. Result: {result is not None} | Data: N/A")
                logger.error(f"[Enricher] Message History Trace:\n{history}")
                logger.error(f"[Enricher] Last Message Raw (first {MAX_HISTORY_TRACE_CHARS} chars): {raw_text[:MAX_HISTORY_TRACE_CHARS]}")
                await self._emit_progress(campaign, "❌ Hệ thống AI không phản hồi đúng định dạng.")
                raise ValueError("AI fail to generate enriched content structure. Check backend logs for trace.")
        else:
            result_data = result.data
            
        logger.info(f"[Enricher] Enrichment successful. Stats: {result_data.stats_added}, Quotes: {result_data.quotes_added}, Tables: {result_data.tables_added}")
        self.current_step = 4
        logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Hoàn tất! Đã chèn {result_data.stats_added} số liệu, {result_data.quotes_added} câu quote và {result_data.tables_added} bảng so sánh. ĐÃ XỬ LÝ XONG")
        await self._emit_progress(campaign, logs[-1])
        logger.warning(f"✅ [ContentEnricher] Phase 4: Injection & Polish Complete.")
        
        # SGE Shield V2.0: Lexical Sanitizer
        new_html = self.clean_ai_html(result_data.new_content)
        new_html = shield_service.sanitize(new_html)
        result_data.new_content = new_html
        
        # CNS V85.24: Reliable Auto-Extraction of items from HTML
        extracted_items = self.detect_items(new_html)
        annotations = self.detect_annotations(new_html)
        
        # Merge AI-reported items with extracted items (use extracted as primary for highlights)
        final_items = extracted_items if extracted_items else result_data.items
        
        # Convert EnrichAIPayload to EnrichResponse
        return EnrichResponse(
            **result_data.model_dump(exclude={"items"}),
            items=final_items,
            annotations=annotations,
            logs=logs
        )

    def _fallback_extract(self, result) -> Optional[EnrichAIPayload]:
        """
        CNS V82.86: Fallback logic to extract data directly from ToolCallPart 
        if PydanticAI fails to map the structured output to result.data.
        """
        if not result or not hasattr(result, "all_messages"):
            return None
            
        try:
            from pydantic_ai.messages import ModelResponse, ToolCallPart
            for msg in reversed(result.all_messages()):
                if isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, ToolCallPart) and part.tool_name == "final_result":
                            logger.info(f"[Enricher] Found tool call 'final_result' in history. Extracting args...")
                            return EnrichAIPayload(**part.args)
        except Exception as e:
            logger.error(f"[Enricher] Fallback extraction failed: {e}")
            
        return None

    @staticmethod
    def detect_items(html: str) -> list[EnrichmentItem]:
        """CNS V85.26: Unified Detection Utility for AI Booster Segments."""
        items = []
        for m in re.finditer(r'<blockquote\s+class="xohi-stat">(.*?)</blockquote>', html, re.DOTALL):
            items.append(EnrichmentItem(type='stat', location='extracted', content=m.group(0)))
        for m in re.finditer(r'<blockquote\s+class="xohi-quote">(.*?)</blockquote>', html, re.DOTALL):
            items.append(EnrichmentItem(type='quote', location='extracted', content=m.group(0)))
        for m in re.finditer(r'<table\s+class="xohi-compare[^"]*">(.*?)</table>', html, re.DOTALL):
            items.append(EnrichmentItem(type='table', location='extracted', content=m.group(0)))
        return items

    @staticmethod
    def detect_annotations(html: str) -> list[SeoAnnotation]:
        """CNS V85.26: Detect AI Booster tags in HTML and return highlights."""
        annotations = []
        def _build_ann(m, label):
            clean_text = re.sub(r'<[^>]*>', ' ', m.group(0))
            clean_text = ' '.join(clean_text.split()).strip()
            return SeoAnnotation(
                type="enrich",
                text=clean_text,
                message=f"🚀 AI Booster: Đã cấy {label} thực tế vào bài viết.",
                severity="info"
            )
        for m in re.finditer(r'<blockquote\s+class="xohi-stat">(.*?)</blockquote>', html, re.DOTALL):
            annotations.append(_build_ann(m, "số liệu"))
        for m in re.finditer(r'<blockquote\s+class="xohi-quote">(.*?)</blockquote>', html, re.DOTALL):
            annotations.append(_build_ann(m, "trích dẫn"))
        for m in re.finditer(r'<table\s+class="xohi-compare[^"]*">(.*?)</table>', html, re.DOTALL):
            annotations.append(_build_ann(m, "bảng so sánh"))
        return annotations

enricher = ContentEnricher()
