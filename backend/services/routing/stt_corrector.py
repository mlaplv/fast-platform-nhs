import os
import json
import logging
import asyncio
import time
import re
from typing import Dict, Optional, Tuple, Set

from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

from .stt_schemas import STTCorrectorDeps, STTCorrectionOutput
from .stt_prompts import STT_CORRECTOR_PROMPT
from .stt_utils import NAV_PATTERNS, NORM_NAV_PATTERNS, SOUND_ALIKES, get_norm
from .stt_neural import NeuralLocalCorrector

logger = logging.getLogger("api-gateway")

class STTCorrector:
    """
    Intelligent layer that cleans transcript using LLM (Trinity).
    Modularized for Martial Law (<300 lines).
    """
    def __init__(self):
        os.environ.pop("GOOGLE_API_KEY", None)
        self.rotator = key_rotator
        self.neural_corrector = NeuralLocalCorrector()
        self._aging_task: Optional[asyncio.Task] = None

        self.agent = Agent(
            deps_type=STTCorrectorDeps,
            output_type=STTCorrectionOutput,
            system_prompt=STT_CORRECTOR_PROMPT
        )

        @self.agent.system_prompt
        def inject_user_dict(ctx: RunContext[STTCorrectorDeps]) -> str:
            if ctx.deps.user_dictionary:
                return f"\n[USER_DICTIONARY_CONTEXT]\n{json.dumps(ctx.deps.user_dictionary, ensure_ascii=False)}"
            return "\n[USER_DICTIONARY_CONTEXT]\n{}"

    async def correct(self, transcript: str, user_dict: Optional[Dict[str, str]] = None, norm_query: Optional[str] = None) -> Tuple[str, Optional[Dict[str, str]]]:
        await self._ensure_aging_task()
        if not transcript: return "", None

        words = transcript.split()
        if len(words) <= 2: return transcript, None
        
        # Fast Bypass for context
        if len(words) <= 4 and any(kw in transcript.lower() for kw in ["bài viết", "sản phẩm", "đơn hàng", "doanh thu", "biểu đồ"]):
            return transcript, None

        if any(kw in transcript.lower() for kw in ["học lệnh", "dạy lệnh", "hoc lenh", "day lenh"]):
            return transcript, None

        # 1. Stopwords
        stopwords = await xohi_memory.get_system_stt_stopwords()
        if stopwords:
            norm_sw = {get_norm(sw) for sw in stopwords}
            filtered = [w for w in words if get_norm(w.lower()) not in norm_sw]
            if len(filtered) < len(words):
                transcript = " ".join(filtered)
                if not transcript: return "", None

        # 2. Neural Local
        sys_overrides = await xohi_memory.get_system_stt_overrides()
        final_dict = {**sys_overrides, **(user_dict or {})}
        neural_cleaned, score = await self.neural_corrector.correct(transcript, final_dict)
        if score >= 0.70: return neural_cleaned, None

        # 3. Pattern / Switch
        norm_q = norm_query or get_norm(transcript)
        if norm_q in NORM_NAV_PATTERNS: return transcript, None

        suspected, applied = {}, False
        lower_t = transcript.lower()
        for wrong, right in SOUND_ALIKES.items():
            if re.search(re.escape(wrong), lower_t, re.I) or get_norm(wrong) in norm_q:
                suspected[wrong.lower()] = right; applied = True
        if applied: return transcript, suspected

        # 4. Trinity Cloud
        try:
            res = await trinity_bridge.run(self.agent, transcript, deps=STTCorrectorDeps(user_dictionary=user_dict or {}))
            out_susp = {i.wrong_word.lower(): i.right_word for i in res.output.suspected_correction} if res.output.suspected_correction else None
            return res.output.cleaned_text, out_susp
        except Exception as e:
            logger.error(f"[STT] Trinity failed: {e}"); return transcript, None

    async def smart_learn(self, user_id: str, wrong: str, right: str, is_global: bool = True):
        norm_w = get_norm(wrong.strip())
        overrides = await xohi_memory.get_system_stt_overrides() if is_global else await xohi_memory.get_stt_dictionary(user_id)
        if norm_w in overrides: return

        # Neural Consolidation
        try:
            await self.neural_corrector._ensure_encoder()
            if self.neural_corrector.encoder:
                def _e(): return list(self.neural_corrector.encoder.embed([norm_w]))
                w_vec = (await asyncio.get_event_loop().run_in_executor(None, _e))[0]
                for ex_w, ex_r in overrides.items():
                    if ex_r == right:
                        e_vec = self.neural_corrector._embedding_cache.get(ex_w)
                        if e_vec is not None and self.neural_corrector._cosine_similarity(w_vec, e_vec) >= 0.95:
                            await xohi_memory.increment_stt_usage(ex_w, is_global); return
        except: pass
        await xohi_memory.learn_stt_correction(user_id, wrong, right, is_global)

    async def _ensure_aging_task(self):
        if not self._aging_task or self._aging_task.done():
            try: self._aging_task = asyncio.create_task(self._neural_aging_loop())
            except RuntimeError: pass

    async def _neural_aging_loop(self):
        while True:
            await asyncio.sleep(3600)
            try: await xohi_memory.prune_stt_overrides(max_size=300)
            except: pass

stt_corrector = STTCorrector()
