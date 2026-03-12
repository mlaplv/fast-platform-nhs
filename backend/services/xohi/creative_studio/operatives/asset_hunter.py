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
Dựa trên tiêu đề và từ khóa của bài viết, hãy lập kế hoạch tìm kiếm hình ảnh chất lượng cao.
Tạo ra 3-5 câu lệnh tìm kiếm (search queries) bằng TIẾNG ANH để tối ưu hóa kết quả từ Google Images.

[QUY TẮC TÌM KIẾM]
1. Ưu tiên phong cách "Professional Photography", "Minimalist", "High Resolution", "Cinematic".
2. Tránh các từ khóa dẫn đến ảnh rác, ảnh chụp màn hình, hoặc ảnh có watermark.
3. Tạo các query đa dạng: Hero/Cover image, Context/Office, Action/Conceptual.
4. Trả về đúng JSON schema."""

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
        
        # Step 2.2: Multi-Query Search & Deduplication
        per_query = max(2, target_count // len(queries) + 1)
        
        for i, q in enumerate(queries):
            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "user_id": str(campaign.user_id),
                "step": 2,
                "message": f"🔍 [Query {i+1}/{len(queries)}] Đang tìm: {q}",
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # pass IDs for visibility
            urls = await self.fetch_images(q, campaign_id=campaign_id, user_id=str(campaign.user_id), num_results=per_query)
            all_urls.extend(urls)
            
            # Deduplicate
            all_urls = list(dict.fromkeys(all_urls))
            if len(all_urls) >= target_count:
                all_urls = all_urls[:target_count]
                break

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

    async def fetch_images(self, query: str, campaign_id: str = None, user_id: str = None, num_results: int = 10) -> List[str]:
        """
        Fetches image URLs from Google.
        Hardened with Circuit Breaker and Key Rotation on 429.
        """
        if self.cooldown_until and datetime.now(timezone.utc) < self.cooldown_until:
            logger.error(f"[AssetHunter] Circuit Breaker Active until {self.cooldown_until}")
            return []

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
                    "num": min(10, num_results),
                    "imgSize": "large" 
                }
                
                logger.info(f"[AssetHunter] Searching index {self.current_index} for: {query}")
                
                if campaign_id:
                    await event_bus.emit("CONTENT_PROGRESS", {
                        "campaign_id": campaign_id,
                        "user_id": user_id,
                        "step": 2,
                        "message": f"🔍 Đang truy quét qua kênh tìm kiếm #{self.current_index + 1}...",
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
                if not items:
                    search_info = data.get('searchInformation', {})
                    total = search_info.get('totalResults', '0')
                    logger.warning(f"[AssetHunter] Key {self.current_index} returned 0 results for '{query}'. Total results: {total}")
                
                urls = [item['link'] for item in items]
                return urls

            except Exception as e:
                logger.error(f"[AssetHunter] Error with key {self.current_index}: {e}")
                self.failure_count += 1
                self._rotate_key()
                attempts += 1
                if attempts >= max_attempts:
                    logger.error("[AssetHunter] All Search API keys exhausted or failed.")
                    self.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES)
                continue
            
        return []
