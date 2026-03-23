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
                except Exception: queries = [f"{primary if primary else title} -text -word"]

            raw_candidates, seen_urls = [], set()
            target_count = int(campaign.get_gold_config().get("max_assets", 10))
            
            for q in queries[:3]:
                if len(raw_candidates) >= target_count * 3: break
                await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": str(campaign.user_id), "step": 2, "message": f"🚀 Thiết giáp săn ảnh: '{q.split(' -')[0]}'...", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
                page_urls = await self.fetch_images(q, campaign_id, str(campaign.user_id), 10)
                for url in page_urls:
                    if url not in seen_urls: seen_urls.add(url); raw_candidates.append(url)

            sem = asyncio.Semaphore(8)
            results = await asyncio.gather(*[check_asset_url(u, sem) for u in raw_candidates])
            valid_urls = [r for r in results if r]
            
            final_assets = [{"id": f"img_{i}_{campaign_id[:4]}", "file_path": url, "is_primary": i == 0, "order_index": i, "media_metadata": {"source": "google"}} for i, url in enumerate(valid_urls[:target_count])]
            
            campaign.assets_data = final_assets
            gold = dict(campaign.gold_metadata or {})
            gold["original_remote_assets"], gold["reserve_assets"] = list(valid_urls[:target_count]), list(valid_urls[target_count:target_count+20])
            campaign.gold_metadata = gold
            flag_modified(campaign, "gold_metadata")
            flag_modified(campaign, "assets_data")
            await repo.update(campaign)
            gc.collect()

            return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message=f"Tìm thấy {len(final_assets)} ảnh.", data={"assets": final_assets})

    async def fetch_images(self, query: str, campaign_id: str, user_id: str, num: int = 10) -> List[str]:
        all_urls = []
        for page in range((num + 9) // 10):
            pair = self.key_pairs[self.current_index]
            try:
                if campaign_id: await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": user_id, "step": 2, "message": f"🔍 Truy quét qua kênh #{self.current_index + 1}...", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
                urls = await fetch_google_page(query, page * 10 + 1, pair)
                all_urls.extend(urls)
                if len(all_urls) >= num or len(urls) < 10: break
            except: 
                self.current_index = (self.current_index + 1) % len(self.key_pairs)
                continue
        return all_urls[:num]
