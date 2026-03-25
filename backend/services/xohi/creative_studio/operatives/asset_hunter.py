from __future__ import annotations
import httpx
import asyncio
import logging
import gc
from typing import List, Optional, Dict, Union, cast
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.event_bus import event_bus
from .asset_hunter_utils import check_asset_url, fetch_google_page
from backend.utils.text import to_int

logger = logging.getLogger("api-gateway")

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search. Standards: V65.0.
    Modularized for Martial Law (<300 lines).
    """
    def __init__(self, key_pairs: List[Dict[str, str]]) -> None:
        logger.info("🚀 [AssetHunter] CNS V82.56 (Ultra Lean 1-Request Mode) Loaded.")
        # Phase 82.50: Increased semaphore from 2 to 5 for higher throughput
        self.key_pairs, self.current_index, self.hunt_semaphore = key_pairs, 0, asyncio.Semaphore(5)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: Union[str, int, float, bool, Dict, List, None]) -> AgentResponse:
        campaign = await repo.get(campaign_id)
        if not campaign: return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found.")

        async with self.hunt_semaphore:
            title = campaign.get_gold_val("title", campaign.source_input)
            primary, ground_truth = campaign.get_gold_val("primary_keyword", ""), campaign.get_gold_val("ground_truth", "")
            
            logger.info(f"📌 [AssetHunter] Starting execute for campaign {campaign_id}")
            await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": str(campaign.user_id), "step": 2, "message": "🧠 Đang lập kế hoạch săn ảnh...", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})

            # CNS V82.56: Extreme Efficiency Optimization (1 Request/Article)
            # Use primary keyword directly instead of AI Planner to save LLM tokens and time
            query = f"{primary if primary else title} -text -word -typography -quote"
            logger.info(f"[AssetHunter] Priority Search (1-Request Mode): {query}")
            
            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id, 
                "user_id": str(campaign.user_id), 
                "step": 2, 
                "message": f"🚀 Thiết giáp săn ảnh (1 Request): '{primary if primary else title}'...", 
                "status": "PROCESSING", 
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Fetch exactly 10 images (1 API Page = 1 Request)
            raw_candidates = await self.fetch_images(query, campaign_id, str(campaign.user_id), 10)
            
            if not raw_candidates:
                logger.warning(f"[AssetHunter] Search yielded 0 results for: {query}")

            sem = asyncio.Semaphore(20) 
            valid_urls = []
            
            target_count = to_int(campaign.get_gold_config().get("max_assets", 10))
            # CNS V82.50: Incremental Waves (V2). Process all but update UI as soon as we have enough for a first look.
            tasks = [check_asset_url(u, sem) for u in raw_candidates]
            
            # Phase 1: Wait for a small set of results to show something to the user quickly
            processed_count = 0
            for coro in asyncio.as_completed(tasks):
                url = await coro
                processed_count += 1
                if url:
                    valid_urls.append(url)
                
                # After 15 candidates checked OR first 5 valid images found, push an early update
                if (processed_count == 15 or len(valid_urls) >= target_count) and len(valid_urls) > 0:
                    temp_assets = [{"id": f"img_{i}_{campaign_id[:4]}", "file_path": u, "is_primary": i == 0, "order_index": i, "media_metadata": {"source": "google"}} for i, u in enumerate(valid_urls[:target_count])]
                    campaign.assets_data = temp_assets
                    await repo.update(campaign)
                    await repo.session.commit()
                    # Emit a pulse to trigger UI frontend sync
                    await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 2, "message": f"🔍 Đã tìm thấy {len(valid_urls)} ảnh chất lượng...", "status": "PROCESSING"})

            primary_slice = valid_urls[:target_count]
            reserve_slice = valid_urls[target_count:target_count+10]
            
            final_assets = [{"id": f"img_{i}_{campaign_id[:4]}", "file_path": url, "is_primary": i == 0, "order_index": i, "media_metadata": {"source": "google"}} for i, url in enumerate(primary_slice)]
            
            campaign.assets_data = final_assets
            gold = dict(campaign.gold_metadata or {})
            gold["assets"] = final_assets 
            gold["reserve_assets"] = reserve_slice
            campaign.gold_metadata = gold
            flag_modified(campaign, "gold_metadata")
            flag_modified(campaign, "assets_data") # Ensure assets_data is marked as modified for the final update
            if not final_assets:
                return AgentResponse(
                    signal=AgentSignal.REDO_PREVIOUS,
                    message="⚠️ Sếp ơi, Google đang chặn em (Rate Limit) hoặc không tìm thấy ảnh nào phù hợp. Sếp thử nhấn 'Chạy lại' nhé!",
                    data={"assets": [], "error": "Search Quota Exceeded or No Results"}
                )

            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message=f"Tìm thấy {len(final_assets)} ảnh (và {len(reserve_slice)} ảnh dự phòng).",
                data={"assets": final_assets, "gold_metadata": gold}
            )

    async def fetch_images(self, query: str, campaign_id: str, user_id: str, num: int = 10, universal: bool = False) -> List[str]:
        all_urls: List[str] = []
        pages_to_fetch = (num + 9) // 10
        
        for page in range(pages_to_fetch):
            attempts = 0
            max_attempts = len(self.key_pairs)
            success = False
            
            while attempts < max_attempts and not success:
                # Phase 82.55: Health Check — Skip dead or currently limited keys
                import time
                now, initial_idx = time.time(), self.current_index
                while self.key_pairs[self.current_index].get("dead") or \
                      cast(float, self.key_pairs[self.current_index].get("limit_until", 0)) > now:
                    self.current_index = (self.current_index + 1) % len(self.key_pairs)
                    if self.current_index == initial_idx: break # All are bad, will raise error via fetch_google_page
                
                pair = self.key_pairs[self.current_index]
                try:
                    if campaign_id: 
                        msg = f"🔍 Truy quét trang {page+1} qua kênh #{self.current_index + 1}{' (Universal)' if universal else ''}..."
                        await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": user_id, "step": 2, "message": msg, "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
                    
                    from backend.constants.agentic import SEARCH_LOCALE_PARAMS
                    params: Dict[str, Union[str, int, float, bool]] = dict(SEARCH_LOCALE_PARAMS)
                    if universal:
                        params.pop("lr", None); params.pop("gl", None)
                    
                    urls = await fetch_google_page(query, page * 10 + 1, pair, override_params=params)
                    all_urls.extend(urls)
                    success = True
                    if len(urls) < 1: break # No more results for this query
                except Exception as e: 
                    # CNS V82.55: Detailed Health Transition
                    error_str = str(e).lower()
                    is_quota = any(x in error_str for x in ["429", "quota", "limit", "rate"])
                    
                    if "403" in error_str and not is_quota:
                        logger.error(f"[AssetHunter] Key index {self.current_index} is FORBIDDEN (403). Marking as DEAD.")
                        self.key_pairs[self.current_index]["dead"] = True
                    else:
                        # 429 or 403-Quota: Cooldown instead of death
                        cooldown = 3600 if "403" in error_str else 900 # 1 hour for 403-Quota, 15m for 429
                        logger.warning(f"[AssetHunter] Key index {self.current_index} rate-limited or quota exceeded. Cooling down for {cooldown}s...")
                        self.key_pairs[self.current_index]["limit_until"] = time.time() + cooldown
                    
                    self.current_index = (self.current_index + 1) % len(self.key_pairs)
                    attempts += 1
                    logger.warning(f"[AssetHunter] Rotating to key index {self.current_index} (Attempt {attempts}/{max_attempts})")
                    await asyncio.sleep(1.0)
            
            if len(all_urls) >= num: break
            
        return all_urls[:num]
