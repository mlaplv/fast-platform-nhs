import httpx
import asyncio
import logging
import re
from typing import List, Optional, Dict, Union
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, quote, urlunparse
from sqlalchemy.orm.attributes import flag_modified

from backend.utils.http_client import get_http_client
from backend.services.event_bus import event_bus
from backend.constants.agentic import MAX_SEARCH_RETRY_PER_STEP, SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import VisualSearchPlan, AgentResponse, AgentSignal

logger = logging.getLogger("api-gateway")

PLANNER_PROMPT = """[ROLE] VISUAL CONTENT DIRECTOR — XoHi Content Factory 2026

[NHIỆM VỤ]
Dựa trên tiêu đề, từ khóa, phong cách và CHẾ ĐỘ NỘI DUNG, hãy tạo duy nhất 01 câu lệnh tìm kiếm (ONE best search query) bằng TIẾNG ANH để tìm hình ảnh MIÊU TẢ CHÍNH XÁC CHỦ THỂ (Subject Accuracy).

[CHIẾN THUẬT THEO CHẾ ĐỘ]
- VIRAL MODE: Tập trung vào cảm xúc, con người, hành động, màu sắc rực rỡ (Cinematic, Vibrant).
- DEEP-DIVE MODE: Tập trung vào tính chuyên nghiệp, bối cảnh thực tế, trừu tượng hóa, sạch sẽ (Professional, Realistic, Clean).

[QUY TẮC ƯU TIÊN - THIẾT QUÂN LUẬT]
1. CHỦ THỂ LÀ SỐ 1 (Subject First): Query BẮT BUỘC phải chứa các từ khóa cốt lõi về thực thể (Giới tính, Độ tuổi, Vật thể, Ngữ cảnh).
2. ANTI-TEXT POLICY: Tuyệt đối dùng từ khóa phủ định để tránh ảnh có chữ: `-text -word -typography -quote -infographic -youtube -video`.
3. STYLE SECOND: Sau khi đảm bảo đúng chủ thể, mới áp dụng phong cách phù hợp với chế độ nội dung.
4. ĐỊNH DẠNG: Trả về JSON VisualSearchPlan với 01 query tối ưu nhất.
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
        
        # R108: Pull Comprehensive Context for Intelligence
        title: str = campaign.get_gold_val("title", campaign.source_input)
        primary: str = campaign.get_gold_val("primary_keyword", "")
        secondary: List[str] = campaign.get_gold_val("secondary_keywords", [])
        persona: str = campaign.get_gold_val("persona", "Professional")
        
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
        try:
            prompt = (
                f"Title: {title}\n"
                f"Primary Keyword: {primary}\n"
                f"Secondary Keywords: {', '.join(secondary)}\n"
                f"Persona: {persona}\n"
                f"Content Mode: {content_mode.upper()}"
            )
            result = await trinity_bridge.run(self.planner_agent, prompt, session_id=campaign.id)
            plan: VisualSearchPlan = result.data if hasattr(result, "data") else result.output
            queries: List[str] = plan.queries
            logger.info(f"[AssetHunter] AI Planner query: {queries[0] if queries else 'None'}")
        except Exception as e:
            logger.error(f"[AssetHunter] AI planning failed, fallback to keywords: {e}")
            queries = [primary if primary else title]

        # Step 2.2: Multi-Query Search & Deduplication
        all_urls = []
        # Professional CTO Fix: Using Standardized Golden Context Helpers
        config = campaign.get_gold_config()
        target_count = int(config.get("max_assets", 10))

        # Step 2.2: Dual-Page Search for Buffer (Efficiency R88)
        # We fetch up to candidate_limit images to ensure enough valid buffer after filtering.
        best_query = queries[0] if queries else (primary if primary else title)

        # V77: Expand buffer for Deep-Dive to ensure enough images for long content
        candidate_limit = 30 if content_mode == "deep_dive" else 20

        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign_id,
            "user_id": str(campaign.user_id),
            "step": 2,
            "message": f"🔍 Đang truy quét ảnh diện rộng ({candidate_limit} candidates): {best_query}",
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Fetch candidate images to provide enough buffer for filtration
        raw_urls = await self.fetch_images(best_query, campaign_id=campaign_id, user_id=str(campaign.user_id), num_results=candidate_limit)

        # Step 2.3: Parallel Anti-YouTube, HTTPS-Only & Integrity Check (Rule R110-V76)
        client = await get_http_client()
        sem = asyncio.Semaphore(8) # Limit concurrency to protect VPS 2GB RAM

        async def _check_url(url: str) -> Optional[str]:
            if not url.startswith("https://"): return None

            skip_domains = ["ytimg.com", "img.youtube.com", "vimeo.com", "fbsbx.com", "fbcdn.net", "licdn.com"]
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

                    # Fallback to GET stream for stubborn CDNs
                    if resp.status_code in [403, 404, 405]:
                        async with client.stream("GET", sanitized_url, timeout=4.0, follow_redirects=True, headers=headers) as stream_resp:
                            if stream_resp.status_code == 200: return url
                except Exception as e:
                    logger.debug(f"[AssetHunter] Parallel check failed for {url}: {e}")
            return None

        # Execute parallel pinging
        tasks = [_check_url(url) for url in raw_urls]
        results = await asyncio.gather(*tasks)
        valid_urls = [r for r in results if r is not None]

        all_urls = valid_urls
        
        # Selection logic based on target_count from Step 1
        if len(all_urls) > target_count:
            logger.info(f"[AssetHunter] Clipping {len(all_urls)} images to target {target_count}")
            all_urls = all_urls[:target_count]
        
        # If too few, we might want to log a warning
        if len(all_urls) < target_count:
            logger.warning(f"[AssetHunter] Found only {len(all_urls)} valid images, target was {target_count}")

        # Step 2.3: Graceful Raw Fallback (Rule R103)
        if not all_urls:
            fallback_query = primary if primary else title
            logger.warning(f"[AssetHunter] All AI queries failed. Triggering CRITICAL FALLBACK: {fallback_query}")
            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "user_id": str(campaign.user_id),
                "step": 2,
                "message": f"⚠️ Truy quét nâng cao thất bại. Chuyển sang chế độ tìm kiếm thô: {fallback_query}",
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            all_urls = await self.fetch_images(fallback_query, campaign_id=campaign_id, user_id=str(campaign.user_id), num_results=target_count)

        campaign.assets_data = all_urls
        # Phase 74: Seed the Golden Thread with original remote URLs for reliable localized replacement in Step 6
        gold = campaign.gold_metadata or {}
        gold["original_remote_assets"] = list(all_urls)
        campaign.gold_metadata = gold
        flag_modified(campaign, "gold_metadata")

        await repo.update(campaign)
        
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign_id,
            "user_id": str(campaign.user_id),
            "step": 2,
            "message": f"✅ Đã tìm thấy {len(all_urls)} ảnh {'chuẩn AI' if queries else 'thô'}. Sẵn sàng duyệt!",
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message=f"Tìm thấy {len(all_urls)} ảnh.",
            data={"assets": all_urls}
        )

    async def fetch_images(self, query: str, campaign_id: str = None, user_id: str = None, num_results: int = 20) -> List[str]:
        """
        Fetches image URLs from Google.
        Supports pagination up to num_results (max 2 requests).
        """
        if self.cooldown_until and datetime.now(timezone.utc) < self.cooldown_until:
            logger.error(f"[AssetHunter] Circuit Breaker Active until {self.cooldown_until}")
            return []

        all_urls = []
        # Google CSE allows max 10 per request. We iterate to fill num_results.
        # R88.5: Fetch at most 20 for buffer balance.
        pages_to_fetch = (num_results + 9) // 10
        
        for page in range(pages_to_fetch):
            start_index = page * 10 + 1
            urls = await self._fetch_page(query, start_index, campaign_id, user_id)
            all_urls.extend(urls)
            if len(urls) < 10: break # No more results
            if len(all_urls) >= num_results: break

        return all_urls[:num_results]

    async def _fetch_page(self, query: str, start: int, campaign_id: str = None, user_id: str = None) -> List[str]:
        url = "https://www.googleapis.com/customsearch/v1"
        attempts = 0
        max_attempts = len(self.key_pairs)
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
                    "imgSize": "large" 
                }
                
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
                return [item['link'] for item in items]

            except Exception as e:
                logger.error(f"[AssetHunter] Search Page Error (Key {self.current_index}): {e}")
                self.failure_count += 1
                self._rotate_key()
                attempts += 1
                continue
            
        return []
