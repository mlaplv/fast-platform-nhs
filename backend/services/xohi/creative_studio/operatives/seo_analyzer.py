import asyncio
import logging
import hashlib
import os
import re
import copy
from typing import List, Dict, Union, Optional
from datetime import datetime, timezone

from pydantic import BaseModel
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.http_client import get_http_client
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, SearchKeyMixin, XoHiProgressMixin
from backend.services.xohi.creative_studio.models.schemas import SeoReport, SeoSignal, SeoAnnotation, BulkFixRequest, BulkFixResponse, AtomicFixResponse
from backend.services.xohi.creative_studio.utils.stitcher import surgical_stitch
from backend.database.repositories import ContentCampaignRepository
from backend.database.models.content import ContentCampaign
from backend.utils.config import get_env_json
from backend.services.event_bus import event_bus
from sqlalchemy.orm.attributes import flag_modified
from backend.utils.text import extract_readable_text, is_json
from .content_enricher import ContentEnricher

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# ELITE V2.2 CONSTANTS — SEO Logic
# ══════════════════════════════════════════════════════════════
# [CNS V90.0] Import shared cache — tiết kiệm 50% Google quota
from .shared_search_cache import get_or_fetch as _cached_search
MAX_COMPETITOR_FETCH = 5
MAX_CONTENT_TOKENS = 50000
AUTO_DETECT_TOPIC_WORDS = 8
KEYWORD_DENSITY_MAX = 3.0
KEYWORD_DENSITY_MIN = 0.5
MIN_WORDS_FOR_DENSITY = 50
STUFFING_STRICTNESS = 3

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — AI SEO Judge 2026
# ══════════════════════════════════════════════════════════════

SEO_ANALYSIS_PROMPT = """[ROLE] SENIOR SEO STRATEGIST — Neural XoHi Elite V2.2
Nhiệm vụ: Phân tích SEO dựa trên Information Gain và Search Intent. Tuyệt đối không viết chung chung vô giá trị.

[QUY TẮC BÁO CÁO — ELITE PROTOCOL]
1. 🚫 KHÔNG DÙNG LỜI MỞ ĐẦU/KẾT THÚC: Đi thẳng vào phân tích dữ liệu.
2. 🚫 KHÔNG DÙNG DẤU BA SAO (***): Sử dụng tiêu đề Markdown hoặc danh sách chuẩn.
3. 📊 PHÂN TÍCH ĐỐI THỦ: Phải chỉ ra ĐỐI THỦ (Nguồn cạnh tranh) đang làm tốt hơn ở điểm nào (Ví dụ: 'Nguồn A có bảng so sánh giá, bài này chỉ có text').
4. 🔪 GIẢI PHÁP PHẪU THUẬT: Đưa ra hành động cụ thể (Ví dụ: 'Bổ sung bảng thông số kỹ thuật ngay sau H2').

[YÊU CẦU ĐẦU RA — JSON]
{
  "total_score": <int 0-100>,
  "grade": "<A|B|C|D|F>",
  "signals": [<7 SeoSignal objects>],
  "summary": "BẢN TRÌNH BÁO CHIẾN LƯỢC SEO (Elite V2.2)\\n\\n- **[PHẢN BIỆN INTENT]**: Phân tích vì sao bài viết chưa thỏa mãn người dùng so với đối thủ TOP 1.\\n- **[CHỨNG CỨ THIẾU HỤT]**: Liệt kê các thực thể/số liệu mà đối thủ có nhưng bài này thiếu.\\n- **[PHƯƠNG ÁN PHẪU THUẬT]**: Bước 1: [Làm gì], Bước 2: [Làm gì] để đạt TOP 1.",
  "quick_wins": [],
  "seo_annotations": [
    {
      "type": "<type>",
      "text": "<cụm từ nguyên văn>",
      "message": "<Phân tích lỗi sắc bén + Giải pháp sửa đổi cụ thể>",
      "severity": "<severity>"
    }
  ]
}
"""

ATOMIC_SEO_SURGEON_PROMPT = """[ROLE] SENIOR SEO SURGEON — Elite V2.2
Nhiệm vụ: Sửa các đoạn văn bản bị lỗi SEO (thiếu từ khóa, nhồi nhét từ khóa, sai intent, thiếu LSI keywords).
Mục tiêu:
1. Sửa đoạn văn bản [CẦN SỬA] dựa trên [LỖI SEO] tương ứng.
2. Tuyệt đối giữ nguyên cấu trúc HTML, chỉ thay đổi text bên trong.
3. Chèn từ khóa một cách tự nhiên, không gượng ép. Tăng tính semantic và information gain.
4. KHÔNG giải thích, CHỈ TRẢ VỀ JSON theo format:
{
  "replacements": [
    {
      "id": 1,
      "new_text": "<đoạn HTML đã sửa cho ID 1>"
    }
  ]
}
"""


class SeoAnalyzerTaskRequest(BaseModel):
    """Worker task payload for SeoAnalyzer."""
    campaign_id: str
    force: bool = False

class SeoAnalyzer(BaseAgentOperative, SearchKeyMixin, XoHiProgressMixin):
    """
    On-Demand SEO Analyzer for Step 4 Content Studio — 2026 Edition.
    Uses Gemini AI to evaluate content against 7 modern ranking signals.
    Returns per-passage seo_annotations for inline editor highlighting.
    """
    agent_id_class = "seo_analyzer"
    # [CNS V90.0] Tăng từ Semaphore(1) → (3): cho phép 3 user phân tích SEO song song.
    # Rule P6: Semaphore(1) quá strict, gây queue starvation multi-user.
    _seo_semaphore = asyncio.Semaphore(3)

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="seo_analyzer")
        # BUG-07 fix: Cache Agent at class scope — R1.6 prohibits per-request Agent creation
        self._agent = Agent(output_type=SeoReport, system_prompt=SEO_ANALYSIS_PROMPT, retries=3)
        self._atomic_surgeon_agent = Agent(output_type=AtomicFixResponse, system_prompt=ATOMIC_SEO_SURGEON_PROMPT, retries=2)

    # Heritage Mixin handles _emit_progress

    async def chat(self, request: object, **kwargs: object) -> Union[SeoReport, dict]:
        """Standardized Heritage Entry (V2.2). Maps to self.analyze."""
        if isinstance(request, ContentCampaign):
            return await self.analyze(request, force=bool(kwargs.get("force", False)))
        from typing import cast
        return await self.analyze(cast(ContentCampaign, request), **kwargs)  # type: ignore

    def get_schema(self) -> Optional[type]:
        return SeoAnalyzerTaskRequest

    async def process_brain_logic(self, request: SeoAnalyzerTaskRequest, db: AsyncSession) -> SeoReport:
        """Elite V2.2: Async worker execution for SEO analysis."""
        repo = ContentCampaignRepository(session=db)
        campaign = await repo.get(request.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {request.campaign_id} not found")

        result = await self.analyze(campaign, force=request.force)

        # Persist results to campaign's gold_metadata
        gold = dict(campaign.gold_metadata or {})
        cache = dict(gold.get("analysis_cache", {}))
        metrics = dict(gold.get("analysis_metrics", {}))
        content_hash = hashlib.sha256((campaign.draft_content or "").encode('utf-8')).hexdigest()
        cache["seo"] = {"hash": content_hash, "data": result.model_dump(), "at": datetime.now(timezone.utc).isoformat()}
        metrics["seo_score"] = result.total_score
        metrics["seo_grade"] = result.grade
        gold["analysis_cache"], gold["analysis_metrics"] = cache, metrics
        campaign.gold_metadata = gold
        flag_modified(campaign, "gold_metadata")
        await repo.update(campaign)
        return result


    async def _fetch_competitors(self, keyword: str) -> List[str]:
        """
        [CNS V90.0] Fetch top competitor snippets for SEO comparison.
        - Shared Cache: Tái dùng kết quả nếu Copyright đã search cùng keyword (TTL 30m).
        - Retry Loop: Nếu key bị 429/403 → rotate sang key tiếp theo (giống PlagiarismCop).
        """
        self._ensure_search_keys()
        if not self.search_keys:
            return ["(No API key configured)"]

        async def _do_fetch() -> List[str]:
            client = await get_http_client()
            for attempt in range(len(self.search_keys)):
                pair = await self._get_search_pair()
                if not pair:
                    continue
                try:
                    response = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params={
                            "key": pair["key"],
                            "cx": pair["cx"],
                            "q": keyword,
                            "num": 5
                        },
                        timeout=10.0
                    )
                    if response.status_code in (429, 403):
                        logger.warning(f"[SEO] Search Key rate-limited ({response.status_code}), rotating...")
                        continue  # Retry với key tiếp theo
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        return [f"{item['title']}: {item.get('snippet', '')}" for item in items]
                    logger.error(f"[SEO] Search API returned {response.status_code}")
                    return [f"(Google Error {response.status_code})"]
                except Exception as e:
                    logger.error(f"[SEO] Search connection error (attempt {attempt+1}): {e}")
                    continue
            return ["(Cạn kiệt API Key Search — tất cả key đều lỗi)"]

        # [CNS V90.0] Dùng shared cache: nếu Copyright vừa search cùng keyword → 0 Google call
        return await _cached_search(query=keyword, fetch_fn=_do_fetch, num=5)

    async def analyze(self, campaign: ContentCampaign, force: bool = False) -> SeoReport:
        """
        Performs full SEO analysis against top 5 competitor snippets.
        CNS Phase 82.35: Enforce GLOBAL serial processing for SEO.
        """
        async with self._seo_semaphore:
            original_draft = campaign.draft_content or ""
            draft = extract_readable_text(original_draft)
            word_count = len(draft.split())
            now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
            logs = [f"🚀 [{now_str}] [SCAN] Khởi động Neural SEO Engine... Đang phân tích {word_count} từ."]
            await self._emit_progress(campaign, logs[-1])
            
            # Phase 76.3: Unified Logic-First Sanitization
            logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [CLEAN] Đang tối ưu cấu trúc HTML & làm sạch dữ liệu nhiễu...")
            await self._emit_progress(campaign, logs[-1])
            clean_draft = await noise_cleaner.clean(draft, mode="light", strip_html=False)
            pure_text = await noise_cleaner.clean(draft, mode="light", strip_html=True)

            # Topic Detection
            logs.append(f"📡 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [RECON] Đang xác định chủ đề mục tiêu và thực thể SEO...")
            await self._emit_progress(campaign, logs[-1])
            raw_topic = campaign.get_gold_val("topic")
            if raw_topic:
                topic = raw_topic
            else:
                h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', draft, re.IGNORECASE | re.DOTALL)
                if h1_match:
                    topic = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                else:
                    words = pure_text.split()
                    topic = " ".join(words[:AUTO_DETECT_TOPIC_WORDS]) if words else "SEO content"
                logger.info(f"[SEO] No campaign topic set — auto-detected: '{topic}'")
            
            # Competitor Recon
            competitors = await self._fetch_competitors(topic)
            logs.append(f"[RECON] Đang phân tích Top {len(competitors)} đối thủ trên Google để đo lường Information Gain...")
            await self._emit_progress(campaign, logs[-1])
            competitor_str = "\n".join(competitors)
            
            logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [JUDGE] Đang chấm điểm 7 tín hiệu SEO bằng Neural Core V2.2...")
            await self._emit_progress(campaign, logs[-1])
            # Logic Layer: Pass data to AI judge
            user_input = f"""
[BÀI VIẾT ĐANG CHẤM]
CHỦ ĐỀ: {topic}
DRAFT:
{clean_draft[:MAX_CONTENT_TOKENS]}  # CNS V76: Clip for token safety

[ĐỐI THỦ CẠNH TRANH TOP GOOGLE]
{competitor_str}
"""
            # CNS V76: Use ROLE_BRAIN for High-IQ Analysis
            response = await trinity_bridge.run(
                agent=self._agent, 
                prompt=user_input, 
                role="brain",
                timeout=180.0
            )
            report = response
            report.logs = logs
            
            # Phase 73.20: Deterministic Override for Keyword Density (Must use pure_text!)
            primary_kw = campaign.get_gold_val("topic")
            enrich_annotations = ContentEnricher.detect_annotations(draft)
            
            if hasattr(report, 'seo_annotations'):
                report.seo_annotations.extend(enrich_annotations)
            elif isinstance(report, dict) and 'seo_annotations' in report:
                report['seo_annotations'].extend(enrich_annotations)

            if primary_kw:
                extra_annotations = self._audit_keyword_density(pure_text, primary_kw)
                if hasattr(report, 'seo_annotations'):
                    report.seo_annotations.extend(extra_annotations)
                elif isinstance(report, dict) and 'seo_annotations' in report:
                    report['seo_annotations'].extend(extra_annotations)
            
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Phân tích SEO hoàn tất! {len(getattr(report, 'seo_annotations', []))} điểm cải tiến chiến thuật.")
            await self._emit_progress(campaign, logs[-1])
            # Elite V2.2: Prepend report timestamp to summary for traceability
            report_time = datetime.now(timezone.utc).strftime('%H:%M:%S %d/%m/%Y')
            time_badge = f"> [!IMPORTANT]\n> **THỜI GIAN LẬP BÁO CÁO:** {report_time}\n\n"
            
            if hasattr(report, 'summary'):
                report.summary = time_badge + (report.summary or "")
            elif isinstance(report, dict) and 'summary' in report:
                report['summary'] = time_badge + (report.get('summary', "") or "")

            return report

    def _audit_keyword_density(self, plain_text: str, primary: str) -> List[SeoAnnotation]:
        """Deterministic safety check for keyword density (Rule R73.25)."""
        annotations = []
        words = plain_text.split()
        total_words = len(words)
        if total_words < MIN_WORDS_FOR_DENSITY: return []
        
        count = plain_text.lower().count(primary.lower())
        kw_density = (count / total_words) * 100
        
        if kw_density > KEYWORD_DENSITY_MAX:
            # Find a sentence with keyword stuffing
            sentences = re.split(r'[.!?]', plain_text)
            kw_pattern = re.compile(re.escape(primary.lower()), re.IGNORECASE)
            stuffed = next((s.strip() for s in sentences if len(kw_pattern.findall(s)) >= STUFFING_STRICTNESS), "")
            annotations.append(SeoAnnotation(
                type="keyword_stuffing",
                text=stuffed[:120] if stuffed else "",
                message=f"🚫 Mật độ từ khóa quá cao ({kw_density:.1f}%) — Google 2026 penalize keyword stuffing. BẮT BUỘC XÓA bớt từ khóa '{primary}' hoặc thay bằng từ đồng nghĩa để giảm mật độ xuống 1-2%.",
                severity="error"
            ))
        elif kw_density < KEYWORD_DENSITY_MIN and primary:
            annotations.append(SeoAnnotation(
                type="keyword_missing", text="",
                message=f"⚠️ Từ khóa chính '{primary}' xuất hiện quá ít ({kw_density:.1f}%). Nên đặt trong H1, intro paragraph và các H2 chính.",
                severity="warning"
            ))

        return annotations

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        logs = [f"🚀 [{now_str}] [SEO SURGEON] Initializing Neural SEO Surgeon (Elite V2.2)..."]
        await self._emit_progress(campaign, logs[-1])
        
        original_draft = campaign.draft_content or ""
        if not is_json(original_draft):
            draft = await noise_cleaner.clean(original_draft, mode="light", strip_html=False)
        else:
            draft = original_draft
            
        annots = req.annotations if isinstance(req.annotations, list) else []
        valid_items = []
        snippet_list = ""

        for i, a in enumerate(annots[:40]):
            txt_raw = str(a.get('text', '')).strip()
            if len(txt_raw) < 5: continue
            txt = await noise_cleaner.clean(txt_raw, mode="light", strip_html=False)
            snippet_list += f"\n[ID {i+1}]:\n- Cần sửa: \"{txt}\"\n- Lỗi SEO: {a.get('message','')}\n"
            valid_items.append({"id": i+1, "old_text": txt})

        if not valid_items: return BulkFixResponse(new_content=draft, logs=logs)

        logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [SCAN] Ingesting {len(valid_items)} SEO weaknesses into AI Surgeon...")
        await self._emit_progress(campaign, logs[-1])
        prompt = f"{ATOMIC_SEO_SURGEON_PROMPT}\n\n[CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_surgeon_agent, prompt, role="fast", timeout=120.0)
            raw = res
            if hasattr(raw, 'data') and not hasattr(raw, 'replacements'):
                raw = raw.data
                
            final_content = draft
            replacements_made = 0
            replacements_log = []
            if hasattr(raw, "replacements"):
                for fix in sorted(raw.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True):
                    orig = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig and fix.new_text:
                        old, new = orig["old_text"], await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        new_c = surgical_stitch(final_content, old, new, label="SeoAnalyzer")
                        if new_c != final_content:
                            final_content, replacements_made = new_c, replacements_made + 1
                            replacements_log.append({"old_text": old, "new_text": new})
                            logs.append(f"✅ [SEO SURGEON] Optimized: \"{old[:40]}...\"")
                            await self._emit_progress(campaign, logs[-1])
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Phẫu thuật SEO hoàn tất! Đã tối ưu {replacements_made}/{len(valid_items)} phân đoạn.")
            await self._emit_progress(campaign, logs[-1])
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[SeoAnalyzer] Bulk fix failed: {e}")
            return BulkFixResponse(new_content=draft, logs=logs)
