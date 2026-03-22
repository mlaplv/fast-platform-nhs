import httpx
import asyncio
import logging
import re
from typing import List, Optional, Dict, Union, cast
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, quote, urlunparse
from sqlalchemy.orm.attributes import flag_modified

from backend.utils.http_client import get_http_client
from backend.services.event_bus import event_bus
from backend.constants.agentic import MAX_SEARCH_RETRY_PER_STEP, SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES, SEARCH_LOCALE_PARAMS
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import VisualSearchPlan, AgentResponse, AgentSignal, ArticleOutline

logger = logging.getLogger("api-gateway")

PLANNER_PROMPT = """[ROLE] CHUYÊN GIA ĐẠO DIỄN HÌNH ẢNH — XoHi Thuần Việt 2026

[NHIỆM VỤ]
Phân tích dữ liệu để tạo 3-5 câu lệnh tìm kiếm (Search queries) bằng TIẾNG VIỆT tập trung vào thực thể sản phẩm/dịch vụ vật lý.

[CHIẾN THUẬT SINH QUERY "SẢN PHẨM THỰC"]
1. ƯU TIÊN THÉP (STEEL PRIORITY): Query 1 BẮT BUỘC phải là sự kết hợp giữa [Tiêu đề] + [Từ khóa chính] để đảm bảo độ chính xác tuyệt đối.
2. BẢO VỆ THƯƠNG HIỆU: Giữ nguyên 100% tên thương hiệu (Vd: "Thương hiệu A"). CẤM DỊCH tên riêng.
3. KHÓA ĐỐI TƯỢNG (SUBJECT-LOCKING): Mọi query BẮT BUỘC phải đi kèm định danh sản phẩm từ Ground Truth (Vd: "chai thuốc [Tên]", "hộp [Tên]", "bao bì [Tên]"). 
   - CẤM Search tên riêng đơn độc (Vd: Không search "Hồng Sơn", phải search "thuốc Hồng Sơn").
4. CHẶN NHIỄU PHI THƯƠNG MẠI: Bắt buộc tránh các bối cảnh Hội nghị, Chính trị, Thể thao nếu đối tượng là Sản phẩm.
5. CHẶN NHIỄU ĐỒ HỌA: Bắt buộc tránh: doll, reindeer, toys, clipart, cartoon, drawing, vector, quote.

[GHI CHÚ] Đừng lo lắng về các bộ lọc phủ định (negative keywords), hệ thống sẽ tự động chèn chúng ở bước hậu kiểm. Hãy tập trung vào việc mô tả đúng thực thể vật lý.

[ĐỊNH DẠNG] Trả về JSON VisualSearchPlan chính xác.
"""

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search API.
    Standards: Subject-First Intelligence (V65.0).
    """
    def __init__(self, key_pairs: List[Dict[str, str]]) -> None:
        self.key_pairs: List[Dict[str, str]] = key_pairs
        self.current_index: int = 0
        self.failure_count: int = 0
        self.cooldown_until: Optional[datetime] = None
        self.use_cache: bool = True # R110: Enable caching for performance.

        # CNS V76: Global-like semaphore for Hunting tasks to protect VPS RAM
        self.hunt_semaphore = asyncio.Semaphore(2)

        # Phase 42: Agent Caching
        self.planner_agent: Agent = Agent(
            output_type=VisualSearchPlan, 
            system_prompt=PLANNER_PROMPT
        )

    def _get_current_pair(self) -> Dict[str, str]:
        if not self.key_pairs:
            raise Exception("No Google Search API Keys configured.")
        return self.key_pairs[self.current_index]

    def _rotate_key(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.key_pairs)
        logger.info(f"[AssetHunter] Rotating key to index {self.current_index}")

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign: Optional[ContentCampaign] = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found.", data={})

        async with self.hunt_semaphore:
            # R108: Pull Comprehensive Context for Intelligence
            title: str = campaign.get_gold_val("title", campaign.source_input)
            primary: str = campaign.get_gold_val("primary_keyword", "")
            secondary: List[str] = campaign.get_gold_val("secondary_keywords", [])
            description: str = campaign.get_gold_val("description", "")
            persona: str = campaign.get_gold_val("persona", "Professional")
            ground_truth: str = campaign.get_gold_val("ground_truth", "")

            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "user_id": str(campaign.user_id),
                "step": 2,
                "message": "🧠 Đang phân tích thực thể và lập kế hoạch săn ảnh...",
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Step 2.1: AI Search Planning (Subject-First Logic)
            content_mode = campaign.get_gold_val("content_mode", "viral")
            
            if content_mode == "normal":
                await event_bus.emit("CONTENT_PROGRESS", {
                    "campaign_id": campaign_id,
                    "user_id": str(campaign.user_id),
                    "step": 2,
                    "message": "⚡ Đang sử dụng từ khóa trực tiếp (Chế độ Thường)...",
                    "status": "PROCESSING",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                # Bypassing AI Planner (R03 Elite: Minimal Latency)
                # Apply standard filters even in normal mode for better stock quality
                base_query = primary if primary else title
                queries = [f"{base_query} -text -word -typography -quote -infographic"]
                logger.info(f"[AssetHunter] Normal Mode: Using direct keywords {queries}")
            else:
                try:
                    prompt = (
                        f"Title: {title}\n"
                        f"Primary Keyword: {primary}\n"
                        f"Secondary Keywords: {', '.join(secondary)}\n"
                        f"Description: {description}\n"
                        f"Persona: {persona}\n"
                        f"Ground Truth: {ground_truth}\n"
                        f"Content Mode: {content_mode.upper()}"
                    )
                    # CNS V76: Reliable unwrapper for Agent results with strict casting
                    result = await trinity_bridge.run(self.planner_agent, prompt, session_id=campaign.id)
                    raw_result = cast(object, result)
                    plan = cast(VisualSearchPlan, getattr(raw_result, "data", getattr(raw_result, "output", raw_result)))
                    raw_queries: List[str] = plan.queries
                    
                    # Phase 15.3: Defensive Post-Processing (Subject-Locking)
                    base_filters = " -text -word -typography -quote -infographic"
                    entity_filters = ""
                    gt_lower = ground_truth.lower()
                    
                    # Expanded Anti-Noise Armor for commercial products
                    if any(word in gt_lower for word in ["thuốc", "dược", "mỹ phẩm", "thực phẩm", "shop", "cửa hàng", "thương hiệu"]):
                        entity_filters = " -hội-nghị -đại-biểu -công-an -quân-đội -bóng-đá -cầu-thủ -chính-trị -văn-kiện -đại-hội"
                    
                    queries: List[str] = []
                    for q in raw_queries:
                        processed_q = q
                        # Force Identifier if missing (V78.0)
                        if "thuốc" in gt_lower and "thuốc" not in q.lower() and "sản phẩm" not in q.lower() and "box" not in q.lower():
                            processed_q = f"thuốc {q}"
                        elif "hồng sơn" in q.lower() and "thuốc" not in q.lower():
                            processed_q = f"sản phẩm {q}"
                            
                        queries.append(f"{processed_q}{base_filters}{entity_filters}")
                        
                    logger.info(f"[AssetHunter] AI Planner (Thiết giáp): {queries}")
                except Exception as e:
                    logger.error(f"[AssetHunter] AI planning failed, fallback to keywords: {e}")
                    fallback_q = primary if primary else title
                    queries = [f"{fallback_q} -text -word -hội-nghị -cầu-thủ"]

            # Step 2.2: Multi-Query Search & Deduplication
            all_urls = []
            config = campaign.get_gold_config()
            target_count = int(config.get("max_assets", 10))

            # Rule R88.6: Multi-Query Expansion for High Recall
            raw_candidates = []
            seen_urls = set()
            candidate_goal = target_count * 3 # Expanded buffer for filtering

            queries_list: List[str] = list(queries)
            for i, q in enumerate(queries_list[:3]): # Try up to 3 best queries
                if len(raw_candidates) >= candidate_goal:
                    break

                # Phase 15.4: Live Intelligence (Thiết giáp reporting)
                display_query = q.split(" -")[0] # Hide negative filters for cleaner UI
                await event_bus.emit("CONTENT_PROGRESS", {
                    "campaign_id": campaign_id,
                    "user_id": str(campaign.user_id),
                    "step": 2,
                    "message": f"🚀 Thiết giáp săn ảnh: '{display_query}'...",
                    "status": "PROCESSING",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                page_results = await self.fetch_images(q, campaign_id=campaign_id, user_id=str(campaign.user_id), num_results=10)
                for url in page_results:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        raw_candidates.append(url)

            # Step 2.3: Parallel Anti-YouTube, HTTPS-Only & Integrity Check (Rule R110-V76)
            client = await get_http_client()
            sem = asyncio.Semaphore(8) # Limit concurrency to protect VPS 2GB RAM

            async def _check_url(url: str) -> Optional[str]:
                if not url.startswith("https://"): return None

                skip_domains = ["ytimg.com", "img.youtube.com", "vimeo.com", "fbsbx.com", "fbcdn.net", "instagram.com", "lookaside.instagram.com", "licdn.com"]
                if any(domain in url.lower() for domain in skip_domains): return None

                async with sem:
                    try:
                        p = urlparse(url)
                        sanitized_url = urlunparse(p._replace(path=quote(p.path), query=quote(p.query, safe='/=&?')))

                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                            "Referer": "https://www.google.com/"
                        }

                        # Try HEAD first
                        resp = await client.head(sanitized_url, timeout=4.0, follow_redirects=True, headers=headers)
                        if resp.status_code == 200: return url

                        # Fallback to GET for stubborn CDNs but only first few bytes
                        if resp.status_code in [403, 404, 405]:
                            async with client.stream("GET", sanitized_url, timeout=4.0, follow_redirects=True, headers=headers) as stream_resp:
                                if stream_resp.status_code == 200: return url
                    except Exception as e:
                        logger.debug(f"[AssetHunter] Parallel check failed for {url}: {e}")
                return None

            # Execute parallel pinging
            tasks = [_check_url(url) for url in raw_candidates]
            results = await asyncio.gather(*tasks)
            valid_urls = [r for r in results if r is not None]

            all_urls = valid_urls
            reserve_urls = []

            # Selection logic based on target_count from Step 1
            if len(all_urls) > target_count:
                logger.info(f"[AssetHunter] Clipping {len(all_urls)} images to target {target_count}")
                reserve_urls = all_urls[target_count:target_count + 20] # Take next 20 as reserve
                all_urls = all_urls[:target_count]

            final_assets = []
            for i, url in enumerate(all_urls):
                final_assets.append({
                    "id": f"img_{i}_{campaign_id[:4]}",
                    "file_path": url,  # R105 Standard alignment
                    "is_primary": i == 0,
                    "order_index": i,
                    "media_metadata": {"source": "google_search"}
                })

            campaign.assets_data = final_assets
            
            # Phase 74: Seed the Golden Thread with original remote URLs
            # R110: Strict typing for JSONB fields
            gold: Dict[str, Union[List[str], Dict[str, object]]] = dict(campaign.gold_metadata or {})
            gold["original_remote_assets"] = list(all_urls)
            gold["reserve_assets"] = list(reserve_urls) # R120: Store reserve candidates
            campaign.gold_metadata = gold
            flag_modified(campaign, "gold_metadata")
            flag_modified(campaign, "assets_data")

            await repo.update(campaign)
            # Memory Discipline: Force GC after asset processing
            import gc
            gc.collect()

            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "user_id": str(campaign.user_id),
                "step": 2,
                "message": f"✅ Đã tìm thấy {len(final_assets)} ảnh {'chuẩn AI' if queries else 'thô'}. Sẵn sàng duyệt!",
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message=f"Tìm thấy {len(final_assets)} ảnh.",
                data={"assets": final_assets}
            )

    async def fetch_images(self, query: str, campaign_id: str = None, user_id: str = None, num_results: int = 20) -> List[str]:
        """
        Fetches image URLs from Google.
        Supports pagination up to num_results (max 2 requests).
        """
        all_urls = []
        pages_to_fetch = (num_results + 9) // 10
        
        # R110: Intelligent Cache Control
        can_use_cache = self.use_cache
        
        for page in range(pages_to_fetch):
            start_index = page * 10 + 1
            urls = await self._fetch_page(query, start_index, campaign_id, user_id)
            all_urls.extend(urls)
            if len(urls) < 10: break # No more results
            if len(all_urls) >= num_results: break

        final_urls = all_urls[:num_results]
        return final_urls

    async def _fetch_page(self, query: str, start: int, campaign_id: str = None, user_id: str = None) -> List[str]:
        url = "https://www.googleapis.com/customsearch/v1"
        attempts: int = 0
        max_attempts: int = len(self.key_pairs)
        client = await get_http_client()
        
        while attempts < max_attempts:
            pair = self._get_current_pair()
            try:
                params = {
                    "key": pair["key"],
                    "cx": pair["cx"],
                    "q": query,
                    "searchType": "image",
                    "num": 10,
                    "start": start,
                    **SEARCH_LOCALE_PARAMS
                }
                
                logger.info(f"[AssetHunter] Parameters for index {self.current_index}: {params}")
                logger.info(f"[AssetHunter] Searching index {self.current_index} (start={start}) for: {query}")
                
                if campaign_id:
                    await event_bus.emit("CONTENT_PROGRESS", {
                        "campaign_id": campaign_id,
                        "user_id": user_id,
                        "step": 2,
                        "message": f"🔍 Đang truy quét qua kênh tìm kiếm #{self.current_index + 1} (trang { (start-1)//10 + 1 })...",
                        "status": "PROCESSING",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                response = await client.get(url, params=params, timeout=10.0)
                
                if response.status_code == 429:
                    logger.warning(f"[AssetHunter] Key index {self.current_index} rate limited (429). Rotating...")
                    self._rotate_key()
                    attempts += 1
                    continue

                response.raise_for_status()
                data = response.json()
                
                self.failure_count = 0
                items = data.get('items', [])
                
                # Phase 16.4: Authentic Guard (>290px dimension filter)
                valid_links = []
                for item in items:
                    img = item.get('image', {})
                    h = int(img.get('height', 0))
                    w = int(img.get('width', 0))
                    
                    if h >= 290 and w >= 290:
                        valid_links.append(item['link'])
                    else:
                        logger.debug(f"[AssetHunter] Dropping small/non-authentic asset: {item['link']} ({w}x{h})")
                
                logger.info(f"[AssetHunter] Found {len(valid_links)}/{len(items)} authentic assets (>290px) for query: {query}")
                return valid_links

            except Exception as e:
                logger.error(f"[AssetHunter] Search Page Error (Key {self.current_index}): {e}")
                self.failure_count += 1
                self._rotate_key()
                attempts += 1
                continue
            
        return []
