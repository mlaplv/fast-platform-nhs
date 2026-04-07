import json
import logging
import asyncio
import re
from typing import Dict, Optional, Tuple

import unicodedata

from pydantic_ai import Agent, RunContext
from rapidfuzz import fuzz

from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from .stt_schemas import STTCorrectorDeps, STTCorrectionOutput
from .stt_prompts import STT_CORRECTOR_PROMPT
from .stt_utils import NORM_NAV_PATTERNS, SOUND_ALIKES, get_norm
from .stt_neural import NeuralLocalCorrector

logger = logging.getLogger("api-gateway")

_COMMAND_WORD_LIMIT = 15  # Sentences shorter than this bypass LLM entirely


class STTCorrector:
    """
    Intelligent layer that cleans transcript using LLM (Trinity).
    Commands (<15 words) are passed verbatim — zero LLM interference.
    Modularized for Martial Law (<300 lines).
    """

    def __init__(self) -> None:
        self.neural_corrector = NeuralLocalCorrector()
        self._aging_task: Optional[asyncio.Task[None]] = None

        self.agent: Agent[STTCorrectorDeps, STTCorrectionOutput] = Agent(
            deps_type=STTCorrectorDeps,
            output_type=STTCorrectionOutput,
            system_prompt=STT_CORRECTOR_PROMPT
        )

        @self.agent.system_prompt
        def inject_user_dict(ctx: RunContext[STTCorrectorDeps]) -> str:
            if ctx.deps.user_dictionary:
                return f"\n[USER_DICTIONARY_CONTEXT]\n{json.dumps(ctx.deps.user_dictionary, ensure_ascii=False)}"
            return "\n[USER_DICTIONARY_CONTEXT]\n{}"

    async def correct(
        self,
        transcript: str,
        user_dict: Optional[Dict[str, str]] = None,
        norm_query: Optional[str] = None,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        await self._ensure_aging_task()
        if not transcript:
            return "", None

        words = transcript.split()
        if len(words) <= 2:
            return transcript, None

        # Fast bypass for short high-intent commands (NFC-normalised)
        t_norm = unicodedata.normalize("NFC", transcript.lower())
        if len(words) <= 12 and any(kw in t_norm for kw in [
            "bài viết", "sản phẩm", "đơn hàng", "doanh thu",
            "doanh số", "biểu đồ", "tạo", "viết bào", "viết bài",
        ]):
            return transcript, None

        if any(kw in t_norm for kw in ["học lệnh", "dạy lệnh", "hoc lenh", "day lenh"]):
            return transcript, None

        # 1. Stopwords
        stopwords = await xohi_memory.get_system_stt_stopwords()
        if stopwords:
            norm_sw = {get_norm(sw) for sw in stopwords}
            filtered = [w for w in words if get_norm(w.lower()) not in norm_sw]
            if len(filtered) < len(words):
                transcript = " ".join(filtered)
                if not transcript:
                    return "", None

        # 2. Neural Local
        sys_overrides = await xohi_memory.get_system_stt_overrides()
        final_dict = {**sys_overrides, **(user_dict or {})}
        neural_cleaned, score = await self.neural_corrector.correct(transcript, final_dict)
        if score >= 0.70:
            return neural_cleaned, None

        # 3. Pattern / Switch
        norm_q = norm_query or get_norm(transcript)
        if norm_q in NORM_NAV_PATTERNS:
            return transcript, None

        suspected: Dict[str, str] = {}
        applied = False
        lower_t = transcript.lower()
        for wrong, right in SOUND_ALIKES.items():
            if right.lower() in lower_t:
                continue
            if re.search(re.escape(wrong), lower_t, re.I) or get_norm(wrong) in norm_q:
                suspected[wrong.lower()] = right
                applied = True
        if applied:
            return transcript, suspected

        # 4. Trinity Cloud — only for long dictation (≥15 words)
        if len(words) < _COMMAND_WORD_LIMIT:
            return transcript, None

        try:
            res = await trinity_bridge.run(
                self.agent,
                transcript,
                deps=STTCorrectorDeps(user_dictionary=user_dict or {}),
                model_settings={"temperature": 0.0},
            )
            c_t = res.cleaned_text
            ratio = fuzz.ratio(transcript.lower(), c_t.lower())
            if ratio < 65:
                logger.warning(f"🚨 [STT] Rejecting hallucination (score={ratio:.1f}): '{transcript}' -> '{c_t}'")
                return transcript, None

            out_susp = {i.wrong_word.lower(): i.right_word for i in res.suspected_correction} if res.suspected_correction else None
            return c_t, out_susp
        except Exception as e:
            logger.error(f"[STT] Trinity failed: {e}")
            return transcript, None

    async def smart_learn(self, user_id: str, wrong: str, right: str, is_global: bool = True) -> None:
        norm_w = get_norm(wrong.strip())
        overrides = (
            await xohi_memory.get_system_stt_overrides() if is_global
            else await xohi_memory.get_stt_dictionary(user_id)
        )
        if norm_w in overrides:
            return

        try:
            await self.neural_corrector._ensure_encoder()
            if self.neural_corrector.encoder:
                def _embed() -> list[object]:
                    return list(self.neural_corrector.encoder.embed([norm_w]))
                w_vec = (await asyncio.get_running_loop().run_in_executor(None, _embed))[0]
                for ex_w, ex_r in overrides.items():
                    if ex_r == right:
                        e_vec = self.neural_corrector._embedding_cache.get(ex_w)
                        if e_vec is not None and self.neural_corrector._cosine_similarity(w_vec, e_vec) >= 0.95:
                            await xohi_memory.increment_stt_usage(ex_w, is_global)
                            return
        except Exception:
            pass
        await xohi_memory.learn_stt_correction(user_id, wrong, right, is_global)

    async def _ensure_aging_task(self) -> None:
        if not self._aging_task or self._aging_task.done():
            try:
                self._aging_task = asyncio.create_task(self._neural_aging_loop())
            except RuntimeError:
                pass

    async def _neural_aging_loop(self) -> None:
        while True:
            await asyncio.sleep(3600)
            try:
                await xohi_memory.prune_stt_overrides(max_size=300)
            except Exception:
                pass


stt_corrector = STTCorrector()
