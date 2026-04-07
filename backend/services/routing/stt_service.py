import logging
import asyncio
import httpx
import unicodedata
from base64 import b64encode
from typing import Dict, Optional, List, cast

from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from .stt_corrector import stt_corrector

logger = logging.getLogger("api-gateway")

class STTService:
    """
    Centralized Gemini STT Service (Elite V3.1).
    Leverages Trinity Orchestration for dynamic model discovery (3.1/2.0/1.5).
    """
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    def get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=100)
            )
        return self._http_client

    async def _get_stt_prompt(self, user_id: Optional[str]) -> str:
        """Standardized STT instructions with contextual anchors."""
        stt_anchors: List[str] = []
        if user_id:
            profile = await xohi_memory.get_voice_profile(user_id)
            if profile:
                stt_anchors = cast(List[str], profile.get("stt_anchors", []))

        system_mapping = await xohi_memory.get_system_intent_mapping()
        system_intents = list(cast(Dict[str, object], system_mapping).keys())[:10] if system_mapping else []
        final_anchors = ", ".join(stt_anchors + system_intents)

        return (
            "Trích xuất chính xác những gì người dùng nói trong đoạn audio bằng tiếng Việt. "
            "KHÔNG ĐƯỢC trả lời, KHÔNG phân tích, KHÔNG thêm bớt từ. "
            f"Gợi ý từ khóa ngữ cảnh: {final_anchors[:500]}"
        )

    async def transcribe(self, audio_data: bytes, user_id: Optional[str] = None) -> str:
        """
        Elite V3.1 dynamic transcription pipeline.
        Standardizes STT with the Trinity Orchestration Engine.
        """
        if not audio_data or len(audio_data) < 100:
            return ""

        # 🛡️ 1. Initialization Guard
        if not trinity_bridge._initialized:
            await trinity_bridge.initialize()

        # 🛡️ 2. Build Dynamic Model Chain (Role: Fast)
        # Includes Gemini 3.1 Flash-Lite, 2.0 Flash, 1.5 Flash based on real-time discovery.
        models = await trinity_bridge.models_helper.build_chain(
            role="fast",
            db_primary=trinity_bridge.db_primary_model or "",
            db_waterfall=trinity_bridge.db_waterfall,
            discovered=trinity_bridge.discovered
        )

        if not models:
            logger.error("🚨 [STT] No models available in Trinity chain.")
            return ""

        # Prepare payload basics
        prompt_text = await self._get_stt_prompt(user_id)
        ext = "webm"
        if audio_data.startswith(b'\x1aE\xdf\xa3'): ext = "webm"
        elif audio_data.startswith(b'OggS'): ext = "ogg"
        elif b'ftyp' in audio_data[:32]: ext = "mp4"

        b64_audio = b64encode(audio_data).decode("utf-8")
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {"inline_data": {"mime_type": f"audio/{ext}", "data": b64_audio}}
                ]
            }],
            "generationConfig": {"temperature": 0.0, "topP": 0.1}
        }

        client = self.get_client()
        last_error = None

        # 🛡️ 3. Execution Loop (Trinity-standard rotation)
        for model_name in models:
            # For FAST tasks, we rotate keys aggressively but don't spam a dying model.
            _MAX_ATTEMPTS = 2 if "3.1" in model_name or "2.0" in model_name else 1
            
            for att in range(_MAX_ATTEMPTS + 1):
                key = await key_rotator.get_key(model_name=model_name)
                if not key: break

                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    logger.debug(f"🧬 [STT] Executing | Model: {model_name} | Key: {key[:8]}... | Att: {att+1}")

                    resp = await client.post(url, json=payload, timeout=15.0)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        await key_rotator.set_success(key)
                        
                        candidates = data.get("candidates", [])
                        if not candidates: return ""
                        
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        normalized = unicodedata.normalize("NFC", raw_text.strip())
                        
                        # 🛡️ 4. Neural Correction (Zero-hallucination)
                        user_dict = await xohi_memory.get_stt_dictionary(user_id) if user_id else None
                        final_text, _ = await stt_corrector.correct(normalized, user_dict)
                        return final_text

                    # Error handling
                    error_payload = {}
                    try: error_payload = resp.json()
                    except: pass
                    
                    error_msg = error_payload.get("error", {}).get("message", resp.text)
                    cat = trinity_bridge.models_helper.classify_error(error_msg)
                    
                    if cat == "rate_limit" or resp.status_code == 429:
                        wait = 1.0 * (2 ** att)
                        logger.warning(f"⚠️ [STT] 429 on {model_name} ({key[:8]}), backing off {wait}s")
                        await key_rotator.mark_unhealthy(key, "rate_limit")
                        await asyncio.sleep(wait)
                        continue
                    
                    if cat in ["auth_hard", "auth_soft"]:
                        await key_rotator.mark_unhealthy(key, cat)
                        continue
                    
                    if cat == "model_not_found":
                        logger.warning(f"❓ [STT] Model {model_name} (404). Skipping.")
                        break
                        
                    logger.error(f"🔥 [STT] Critical Error [{resp.status_code}] on {model_name}: {error_msg}")
                    break

                except Exception as e:
                    last_error = e
                    logger.error(f"💥 [STT] Exception on {model_name}: {e}")
                    break

        # 🛡️ 5. Emergency Recovery
        logger.error(f"🚨 [STT] TOTAL PIPELINE OUTAGE. Last error: {last_error}")
        await key_rotator.reset_health()
        return ""

stt_service = STTService()
