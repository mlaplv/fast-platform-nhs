import logging
import asyncio
import gc
from typing import List, Dict, Union, Optional, Tuple
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.text import to_int
from backend.utils.noise_cleaner import noise_cleaner
from .creative_pen_prompts import OUTLINE_PROMPT, DRAFT_PROMPT
from .creative_pen_utils import process_pen_draft

logger = logging.getLogger("api-gateway")

class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content. V62.1.
    Modularized for Martial Law (<300 lines).
    """
    def __init__(self, model_name: Optional[str] = None):
        logger.info("🔥 [CreativePen] CNS V82.55 Loaded with to_int protection.")
        self.model_name, self.pen_semaphore = model_name, asyncio.Semaphore(1)
        self.outline_agent = Agent(output_type=ArticleOutline, system_prompt=OUTLINE_PROMPT, retries=3)
        self.draft_agent = Agent(system_prompt=DRAFT_PROMPT)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        campaign = await repo.get(campaign_id)
        if not campaign: return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")

        async with self.pen_semaphore:
            step = kwargs.get("step")
            logger.info(f"🖊️ [CreativePen] Executing Step {step} for {campaign_id}")
            if step == 3:
                logger.info(f"📝 [CreativePen] Generating Outline for {campaign_id}")
                outline = await self.generate_outline(campaign)
                campaign.outline_data = outline.model_dump() if isinstance(outline, ArticleOutline) else outline
                return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Outline generated.", data=campaign.outline_data)
            elif step == 4:
                logger.info(f"🖋️ [CreativePen] Writing Draft for {campaign_id}")
                content = await self.write_draft(campaign)
                campaign.draft_content = content
                return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Draft generated.", data={"content": content})
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step}")

    async def generate_outline(self, campaign: ContentCampaign) -> Union[ArticleOutline, Dict[str, object], None]:
        config = campaign.get_gold_config()
        t, p = campaign.get_gold_val("title", ""), campaign.get_gold_val("primary_keyword", "")
        gt = campaign.get_gold_val("ground_truth", "")
        max_s = to_int(config.get("max_sections", 3))
        
        inst = f"Hãy tạo Dàn Ý (ArticleOutline) chi tiết gồm đúng {max_s} mục H2. Bám sát Ground Truth."
        prompt = f"Tiêu đề: {t}\nTừ khóa: {p}\nGround Truth: {gt}\nGiới hạn: {max_s} mục H2."
        
        try:
            res = await trinity_bridge.run(self.outline_agent, f"{inst}\n{prompt}", session_id=campaign.id, model=self.model_name)
            raw = getattr(res, "data", getattr(res, "output", res))
            if isinstance(raw, ArticleOutline): return raw
            if isinstance(raw, dict) and "sections" in raw: return ArticleOutline(**raw)
            return raw
        except Exception as e:
            logger.error(f"[CreativePen] Outline Error: {e}")
            raise

    async def write_draft(self, campaign: ContentCampaign) -> str:
        prompt, assets, primary = await self._build_p(campaign)
        try:
            res = await trinity_bridge.run(self.draft_agent, prompt, session_id=campaign.id, model=self.model_name)
            raw = getattr(res, "data", getattr(res, "output", str(res)))
            return await process_pen_draft(str(raw), assets, primary)
        except Exception as e:
            logger.error(f"[CreativePen] Draft Error: {e}"); raise

    async def stream_draft(self, campaign: ContentCampaign):
        prompt, assets, primary = await self._build_p(campaign)
        try:
            full_raw = ""
            async with trinity_bridge.run_stream(self.draft_agent, prompt, session_id=campaign.id, model=self.model_name) as stream:
                async for text in stream.stream_text(delta=True):
                    if text: full_raw += text; yield {"type": "chunk", "text": text}
            yield {"type": "final", "content": await process_pen_draft(full_raw, assets, primary)}
        except Exception as e:
            logger.error(f"[CreativePen] Stream Error: {e}"); yield {"type": "error", "message": str(e)}; raise

    async def _build_p(self, campaign: ContentCampaign) -> Tuple[str, List[str], str]:
        outline_data = campaign.outline_data or {}
        assets = campaign.assets_data or []
        p = campaign.get_gold_val("primary_keyword", "chủ đề")
        t, gt = campaign.get_gold_val("title", p), campaign.get_gold_val("ground_truth", "")
        
        sections = outline_data.get("sections", []) if isinstance(outline_data, dict) else []
        outline_text = "\n".join([f"- {s.get('heading', '')}: {s.get('content', '')}" for s in sections]) if sections else f"H2: {t}"
        
        clean_assets = [a.get("file_path") or a.get("url") or str(a) if isinstance(a, dict) else (getattr(a, "file_path", getattr(a, "url", str(a)))) for a in assets]
        asset_ctx = "\n".join([f"[IMAGE_{i}]: {url}" for i, url in enumerate(clean_assets[:12], 1)]) or "(Không có ảnh)"
        
        config = campaign.get_gold_config()
        target_w = min(max(to_int(config.get("word_count", 500)), 100), 2500)
        max_s = to_int(config.get("max_sections", 3))
        mode = config.get("content_mode", "viral")
        
        p_per_s = 4 if mode == "deep_dive" else (2 if mode == "normal" else (1 if max_s >= 8 else 2))
        limit = max_s * (5 if mode == "deep_dive" else (3 if mode == "normal" else 2))

        prompt = f"""
[GOLDEN THREAD] Tiêu đề: {t} | Từ khóa: {p} | GT: {gt} | Chế độ: {mode.upper()}
[DÀN Ý] {outline_text}
[KHO ẢNH] {asset_ctx}
[YÊU CẦU] <h1>{t}</h1> | Mục tiêu: {target_w} từ | Max {p_per_s} đoạn/mục | Tổng max {limit} đoạn <p>.
Chèn [IMAGE_N]. Trả về HTML thuần. Không giải thích.
"""
        return prompt, clean_assets, p
