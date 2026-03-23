import httpx
import asyncio
import logging
import gc
from typing import List, Optional, Dict, Union, cast
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import VisualSearchPlan, AgentResponse, AgentSignal
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from .asset_hunter_prompts import PLANNER_PROMPT
from .asset_hunter_utils import check_asset_url, fetch_google_page

logger = logging.getLogger("api-gateway")

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search. Standards: V65.0.
    Modularized for Martial Law (<300 lines).
    """
    def __init__(self, key_pairs: List[Dict[str, str]]) -> None:
        self.key_pairs, self.current_index, self.hunt_semaphore = key_pairs, 0, asyncio.Semaphore(2)
        self.planner_agent = Agent(output_type=VisualSearchPlan, system_prompt=PLANNER_PROMPT)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        campaign = await repo.get(campaign_id)
        if not campaign: return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found.")

        async with self.hunt_semaphore:
            title = campaign.get_gold_val("title", campaign.source_input)
            primary, ground_truth = campaign.get_gold_val("primary_keyword", ""), campaign.get_gold_val("ground_truth", "")
            
            await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": str(campaign.user_id), "step": 2, "message": "🧠 Đang lập kế hoạch săn ảnh...", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})

            content_mode, queries = campaign.get_gold_val("content_mode", "viral"), []
            if content_mode == "normal":
                queries = [f"{primary if primary else title} -text -word -typography -quote"]
            else:
                try:
                    res = await trinity_bridge.run(self.planner_agent, f"Title: {title}\nPrimary: {primary}\nGT: {ground_truth}", session_id=campaign.id)
                    raw_res = getattr(res, "data", getattr(res, "output", res))
                    base_f, ent_f = " -text -word -quote", (" -hội-nghị -chính-trị" if "thuốc" in ground_truth.lower() else "")
                    queries = [f"{q}{base_f}{ent_f}" for q in raw_res.queries]
                    logger.info(f"[AssetHunter] AI Planner generated {len(queries)} queries.")
                except Exception as e: 
                    logger.error(f"[AssetHunter] AI Planner failed: {e}")
                    queries = [f"{primary if primary else title} -text -word"]

            # V82.35: Safety guard if AI returns empty queries
            if not queries:
                 queries = [f"{primary if primary else title} -text -word"]

            raw_candidates, seen_urls = [], set()
            target_count = int(campaign.get_gold_config().get("max_assets", 10))
            if target_count < 3: # CNS V82.35: Safety Floor — Sếp yêu cầu luôn có tối đa 10, tối thiểu 3
                target_count = 10
            
            logger.info(f"[AssetHunter] Target Asset Count: {target_count}")
            
            for q in queries[:3]:
                if len(raw_candidates) >= target_count * 4: break # CNS V82.36: Increased from 3x to 4x for better reserve
                display_q = q.split(' -')[0]
                logger.info(f"[AssetHunter] Targeted Search: {display_q}")
                await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": str(campaign.user_id), "step": 2, "message": f"🚀 Thiết giáp săn ảnh: '{display_q}'...", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
                page_urls = await self.fetch_images(q, campaign_id, str(campaign.user_id), 15) # CNS V82.36: Increased from 10 to 15
                if not page_urls:
                    logger.warning(f"[AssetHunter] Search yielded 0 results for: {display_q}")
                for url in page_urls:
                    if url not in seen_urls: seen_urls.add(url); raw_candidates.append(url)

            # CNS Phase 82.30: Emergency fallback if no candidates found
            if not raw_candidates:
                fallback_q = f"{primary if primary else title} high quality"
                logger.warning(f"[AssetHunter] Emergency fallback search: {fallback_q}")
                page_urls = await self.fetch_images(fallback_q, campaign_id, str(campaign.user_id), 20, universal=True) # CNS V82.36: Increased from 15 to 20
                for url in page_urls:
                    if url not in seen_urls: seen_urls.add(url); raw_candidates.append(url)

            sem = asyncio.Semaphore(20) 
            valid_urls = []
            
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

            logger.info(f"[AssetHunter] Final valid images found: {len(valid_urls)}")
            
            primary_slice = valid_urls[:target_count]
            reserve_slice = valid_urls[target_count:target_count+20]
            
            final_assets = [{"id": f"img_{i}_{campaign_id[:4]}", "file_path": url, "is_primary": i == 0, "order_index": i, "media_metadata": {"source": "google"}} for i, url in enumerate(primary_slice)]
            
            campaign.assets_data = final_assets
            gold = dict(campaign.gold_metadata or {})
            gold["assets"] = final_assets 
            gold["reserve_assets"] = reserve_slice
            campaign.gold_metadata = gold
            flag_modified(campaign, "gold_metadata")
            flag_modified(campaign, "assets_data") # Ensure assets_data is marked as modified for the final update
            await repo.update(campaign)
            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message=f"Tìm thấy {len(final_assets)} ảnh (và {len(reserve_slice)} ảnh dự phòng).",
                data={"assets": final_assets, "gold_metadata": gold}
            )

    async def fetch_images(self, query: str, campaign_id: str, user_id: str, num: int = 10, universal: bool = False) -> List[str]:
        all_urls = []
        pages_to_fetch = (num + 9) // 10
        
        for page in range(pages_to_fetch):
            attempts = 0
            max_attempts = len(self.key_pairs)
            success = False
            
            while attempts < max_attempts and not success:
                pair = self.key_pairs[self.current_index]
                try:
                    if campaign_id: 
                        msg = f"🔍 Truy quét trang {page+1} qua kênh #{self.current_index + 1}{' (Universal)' if universal else ''}..."
                        await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": user_id, "step": 2, "message": msg, "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
                    
                    from backend.constants.agentic import SEARCH_LOCALE_PARAMS
                    params = dict(SEARCH_LOCALE_PARAMS)
                    if universal:
                        params.pop("lr", None); params.pop("gl", None)
                    
                    urls = await fetch_google_page(query, page * 10 + 1, pair, override_params=params)
                    all_urls.extend(urls)
                    success = True
                    if len(urls) < 1: break # No more results for this query
                except Exception as e: 
                    # CNS V82.50: Softened from ERROR to WARNING as this is handled by rotation
                    logger.warning(f"[AssetHunter] Key index {self.current_index} rate-limited or failed: {e}")
                    self.current_index = (self.current_index + 1) % len(self.key_pairs)
                    attempts += 1
                    logger.warning(f"[AssetHunter] Rotating to key index {self.current_index} (Attempt {attempts}/{max_attempts})")
                    await asyncio.sleep(1.0) # V82.36: Increased cooldown to 1s for better quota recovery
            
            if len(all_urls) >= num: break
            
        return all_urls[:num]
