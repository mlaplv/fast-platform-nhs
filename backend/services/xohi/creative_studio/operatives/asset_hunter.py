import httpx
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
from backend.utils.http_client import get_http_client
from backend.services.event_bus import event_bus
from backend.constants.agentic import MAX_SEARCH_RETRY_PER_STEP, SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import VisualSearchPlan

logger = logging.getLogger("api-gateway")

PLANNER_PROMPT = """[ROLE] VISUAL CONTENT DIRECTOR — XoHi Content Factory 2026

[NHIỆM VỤ]
Dựa trên tiêu đề và từ khóa bài viết PR Viral, hãy tạo duy nhất 01 câu lệnh tìm kiếm (ONE best search query) bằng TIẾNG ANH để tìm hình ảnh MIÊU TẢ CẢNH THỰC (Real Scene).

[QUY TẮC BẮT BUỘC - ANTI-TEXT POLICY]
1. TUYỆT ĐỐI KHÔNG tìm ảnh có chữ, văn bản, trích dẫn (quotes), hoặc infographic. 
2. Sử dụng các từ khóa phủ định (negative keywords) trong query như: `-text`, `-word`, `-typography`, `-quote`, `-infographic`, `-youtube`, `-video`.
3. Ưu tiên phong cách: "Cinematic photography", "Authentic lifestyle", "High-end stock", "Clean background", "No text".
4. Ảnh phải có chiều sâu, ánh sáng chuyên nghiệp, không được giống ảnh chụp màn hình hay ảnh rác.

[ĐỊNH DẠNG ĐẦU RA]
Trả về đúng JSON schema VisualSearchPlan với duy nhất 01 phần tử trong danh sách `queries`."""

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search API.
    Upgraded with AI Visual Search Planning (V64.2).
    Hardened with Key Rotator and Circuit Breaker (Rule 7).
    """
    def __init__(self, key_pairs: List[Dict[str, str]]):
        """
        key_pairs: List of {"key": "...", "cx": "..."}
        """
        self.key_pairs = key_pairs
        self.current_index = 0
        self.failure_count = 0
        self.cooldown_until: Optional[datetime] = None
        
        # Phase 42: Professional Agent Caching (Memory Discipline)
        self.planner_agent = Agent(
            output_type=VisualSearchPlan, 
            system_prompt=PLANNER_PROMPT
        )

    def _get_current_pair(self) -> Dict[str, str]:
        if not self.key_pairs:
            raise Exception("No Google Search API Keys configured.")
        return self.key_pairs[self.current_index]

    def _rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.key_pairs)
        logger.info(f"[AssetHunter] Rotating to key index {self.current_index}")

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs):
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign: return
        
        # Professional CTO Fix: Using Standardized Golden Context Helpers
        title = campaign.get_gold_val("title", campaign.source_input)
        primary = campaign.get_gold_val("primary_keyword", "")
        
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign_id,
            "user_id": str(campaign.user_id),
            "step": 2,
            "message": "🧠 Đang khởi tạo Creative Director để lập kế hoạch hình ảnh...",
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Step 2.1: AI Search Planning
        try:
            prompt = f"Tiêu đề: {title}\nTừ khóa chính: {primary}"
            result = await trinity_bridge.run(self.planner_agent, prompt)
            plan: VisualSearchPlan = result.data if hasattr(result, "data") else result.output
            queries = plan.queries
            logger.info(f"[AssetHunter] AI generated {len(queries)} search queries.")
        except Exception as e:
            logger.error(f"[AssetHunter] AI planning failed, falling back to raw keyword: {e}")
            queries = [primary if primary else title]

        # Step 2.2: Multi-Query Search & Deduplication
        all_urls = []
        # Professional CTO Fix: Using Standardized Golden Context Helpers
        config = campaign.get_gold_config()
        target_count = config.get("max_assets", 10)
        
        # Step 2.2: Dual-Page Search for Buffer (Efficiency R88)
        # We fetch up to 20 images (2 pages) to ensure enough valid buffer after filtering.
        best_query = queries[0] if queries else (primary if primary else title)
        
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign_id,
            "user_id": str(campaign.user_id),
            "step": 2,
            "message": f"🔍 Đang truy quét ảnh diện rộng (20 candidates): {best_query}",
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Fetch 20 images to provide enough buffer for filtration (YT thumbnails, dead links, hotlink protection)
        raw_urls = await self.fetch_images(best_query, campaign_id=campaign_id, user_id=str(campaign.user_id), num_results=20)
        
        # Step 2.3: Anti-YouTube, HTTPS-Only & Integrity Check (Rule R110)
        valid_urls = []
        client = await get_http_client()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }
        
        skip_domains = ["ytimg.com", "img.youtube.com", "vimeo.com", "fbsbx.com", "fbcdn.net", "licdn.com"]
        
        for url in raw_urls:
            # Rule R112: Force HTTPS (Avoid Mixed Content)
            if not url.startswith("https://"):
                logger.info(f"[AssetHunter] Skipping non-HTTPS URL: {url}")
                continue

            # Skip video thumbnails & Unstable social links
            if any(domain in url.lower() for domain in skip_domains):
                logger.info(f"[AssetHunter] Skipping unstable/video domain: {url}")
                continue
                
            try:
                # Sanitize URL for httpx (Fixes 'illegal request line')
                from urllib.parse import urlparse, quote, urlunparse
                p = urlparse(url)
                sanitized_url = urlunparse(p._replace(path=quote(p.path), query=quote(p.query, safe='/=&?')))

                # Ping URL (Rule R111: Link Integrity)
                # First try HEAD (Fast)
                resp = await client.head(sanitized_url, timeout=4.0, follow_redirects=True, headers=headers)
                
                # If HEAD is 403 or 405 (Many CDNs block HEAD), try GET (with stream to avoid downloading full image)
                if resp.status_code in [403, 404, 405]:
                    async with client.stream("GET", sanitized_url, timeout=4.0, follow_redirects=True, headers=headers) as stream_resp:
                        if stream_resp.status_code == 200:
                            valid_urls.append(url)
                        continue # End processing this URL
                
                if resp.status_code == 200:
                    valid_urls.append(url)
                else:
                    logger.warning(f"[AssetHunter] Link rejected ({resp.status_code}): {url}")
            except Exception as e:
                logger.warning(f"[AssetHunter] Integrity check failed for {url}: {e}")
                
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
        from sqlalchemy.orm.attributes import flag_modified
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
