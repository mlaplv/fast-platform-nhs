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
from .creative_pen_prompts import PROMPTS
from .creative_pen_utils import process_pen_draft

logger = logging.getLogger("api-gateway")

class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content. V62.1.
    CNS V85.1: Multi-Entity Support (News vs Product).
    """
    def __init__(self, model_name: Optional[str] = None):
        logger.info("🔥 [CreativePen] CNS V85.1 Multi-Entity Engine Loaded.")
        self.model_name, self.pen_semaphore = model_name, asyncio.Semaphore(1)
        # We'll initialize agents dynamically or with base prompts
        self.outline_agent = Agent(output_type=ArticleOutline, retries=3)
        self.draft_agent = Agent()

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
                
                # CNS V82.1: Immediate memory release for 2GB VPS safety
                del content
                gc.collect()
                
                return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Draft generated.", data={"content": campaign.draft_content})
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step}")

    async def generate_outline(self, campaign: ContentCampaign) -> Union[ArticleOutline, Dict[str, object], None]:
        config = campaign.get_gold_config()
        t, p = campaign.get_gold_val("title", ""), campaign.get_gold_val("primary_keyword", "")
        gt = campaign.get_gold_val("ground_truth", "")
        max_s = to_int(config.get("max_sections", 3))
        
        # CNS V85.1: Adaptive Prompting
        ent = config.get("target_entity", "article")
        system_prompt = PROMPTS.get(ent, PROMPTS["article"])["outline"]
        
        inst = f"Hãy tạo Dàn Ý (ArticleOutline) chi tiết gồm đúng {max_s} mục H2. Bám sát Ground Truth."
        prompt = f"Tiêu đề: {t}\nTừ khóa: {p}\nGround Truth: {gt}\nGiới hạn: {max_s} mục H2."
        
        try:
            res = await trinity_bridge.run(
                self.outline_agent, f"{inst}\n{prompt}", 
                system_prompt=system_prompt,
                session_id=campaign.id, model=self.model_name
            )
            raw = getattr(res, "data", getattr(res, "output", res))
            if isinstance(raw, ArticleOutline): return raw
            if isinstance(raw, dict) and "sections" in raw: return ArticleOutline(**raw)
            return raw
        except Exception as e:
            logger.error(f"[CreativePen] Outline Error: {e}")
            raise

    async def write_draft(self, campaign: ContentCampaign) -> str:
        config = campaign.get_gold_config()
        ent = config.get("target_entity", "article")
        system_prompt = PROMPTS.get(ent, PROMPTS["article"])["draft"]
        
        prompt, assets, primary = await self._build_p(campaign)
        try:
            res = await trinity_bridge.run(
                self.draft_agent, prompt, 
                system_prompt=system_prompt,
                session_id=campaign.id, model=self.model_name
            )
            raw = getattr(res, "data", getattr(res, "output", str(res)))
            content = await process_pen_draft(str(raw), assets, primary)
            
            # CNS V85.1: Extract Metadata for Products
            if ent == "product":
                content = self._extract_xohi_metadata(content, campaign)
                
            return content
        except Exception as e:
            logger.error(f"[CreativePen] Draft Error: {e}"); raise

    async def stream_draft(self, campaign: ContentCampaign):
        config = campaign.get_gold_config()
        ent = config.get("target_entity", "article")
        prompt, assets, primary = await self._build_p(campaign)
        try:
            full_raw = ""
            async with trinity_bridge.run_stream(self.draft_agent, prompt, session_id=campaign.id, model=self.model_name) as stream:
                async for text in stream.stream_text(delta=True):
                    if text: full_raw += text; yield {"type": "chunk", "text": text}
            
            final_content = await process_pen_draft(full_raw, assets, primary)
            if ent == "product":
                final_content = self._extract_xohi_metadata(final_content, campaign)
                
            yield {"type": "final", "content": final_content}
            
            # CNS V82.1: Clear massive streaming buffers
            del full_raw
            del final_content
            gc.collect()
            
        except Exception as e:
            logger.error(f"[CreativePen] Stream Error: {e}"); yield {"type": "error", "message": str(e)}; raise

    def _extract_xohi_metadata(self, content: str, campaign: ContentCampaign) -> str:
        """CNS V85.1: Neural Metadata Extraction (Regex based)."""
        import re
        import json
        from sqlalchemy.orm.attributes import flag_modified
        
        match = re.search(r'<xohi-metadata>(.*?)</xohi-metadata>', content, re.DOTALL)
        if match:
            try:
                meta = json.loads(match.group(1).strip())
                gold = dict(campaign.gold_metadata or {})
                
                # Sync attributes, price, seo
                for key in ["attributes", "price", "seo_title", "seo_description"]:
                    if key in meta:
                        gold[key] = meta[key]
                
                campaign.gold_metadata = gold
                flag_modified(campaign, "gold_metadata")
                logger.info(f"✅ [CreativePen] Metadata extracted for {campaign.id}")
            except Exception as e:
                logger.error(f"❌ [CreativePen] Metadata Parse Error: {e}")
            
            # Clean HTML
            content = re.sub(r'<xohi-metadata>.*?</xohi-metadata>', '', content, flags=re.DOTALL).strip()
            
        return content

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
