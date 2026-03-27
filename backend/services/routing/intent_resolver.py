import logging, time, unicodedata, re, json
from rapidfuzz import fuzz
from typing import List, Dict, Optional
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.utils.text import normalize_vn, sanitize_id
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.semantic_router import SemanticRouter, INTENT_TO_ACTION
from .stt_corrector import stt_corrector
from .heuristic_classifier import heuristic_classify
from .intent_synapse import intent_synapse
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import ContentCampaignRepository
from backend.services.ai_engine.core.vector_memory import VectorMemory

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

# Constants moved from orchestrator
WAKE_TRIGGERS = ["xohi", "so hi", "xo hi", "số hi", "xố hỉ", "số hỉ", "so huy", "số huy", "chao", "xin chao"]
SLEEP_TRIGGERS = ["cut", "ngu di", "thoat", "tam biet", "bye"]
NORM_WAKE_TRIGGERS = [normalize_vn(kw) for kw in WAKE_TRIGGERS]
NORM_SLEEP_TRIGGERS = [normalize_vn(kw) for kw in SLEEP_TRIGGERS]
YES_KEYWORDS = ["đúng", "vâng", "yes", "ừ", "ok", "ok đi", "chuẩn", "đươc", "rồi", "chính xác", "phải", "phai", "có"]
NO_KEYWORDS = ["không", "nhầm", "sai", "no"]
NAV_KEYWORDS = ["mở", "xem", "vào", "biểu đồ", "show", "open", "display", "chart", "bi do", "bí đồ"]
NORM_YES_KEYWORDS = {normalize_vn(kw) for kw in YES_KEYWORDS}
NORM_NO_KEYWORDS = {normalize_vn(kw) for kw in NO_KEYWORDS}

class RouterResolver:
    """Phase 1: Intent Resolution (T1 -> T2 Dispatch)."""
    def __init__(self, semantic_router, t2_router):
        self.semantic_router = semantic_router
        self.t2_router = t2_router

    async def classify(self, transcript: str, user_id: str, app_state: dict, context=None, screen_context=None, modality="text") -> IntentResponse:
        t0 = time.monotonic()
        user_id = sanitize_id(user_id) or "default"
        transcript = unicodedata.normalize('NFC', transcript.strip())
        t_low = transcript.lower()
        norm_t = normalize_vn(t_low)
        t_pho = norm_t.replace("k", "c").replace("q", "c")

        o_ctx = await xohi_memory.get_full_orchestrator_context(user_id)
        profile, ctx, u_dict, i_map = o_ctx.get("profile", {}), o_ctx.get("ctx", {}), o_ctx.get("stt", {}), o_ctx.get("intent_map", {})

        # Wake/Sleep Logic
        is_wake = self._match(profile.get("wake_words", []) + NORM_WAKE_TRIGGERS, norm_t, t_pho)
        is_sleep = self._match(profile.get("sleep_words", []) + NORM_SLEEP_TRIGGERS, norm_t, t_pho)

        if is_wake:
            rem = await self._strip_wake(transcript, profile.get("wake_words", []) + WAKE_TRIGGERS)
            if rem: transcript, t_low, norm_t = rem, rem.lower(), normalize_vn(rem.lower())
            else: return await self._handle_wake(user_id, profile.get("greeting_template", "Dạ?"))

        if is_sleep and len(transcript.split()) <= 2:
            return IntentResponse(status="success", action=IntentAction.READ, message="Hẹn gặp lại sếp.", router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "HARDWARE_SLEEP"})

        # STT Confirm
        if ctx.get("is_confirming_stt"):
            return await self._handle_stt_confirm(user_id, ctx, norm_t, u_dict, profile, i_map)

        # Normal Flow
        h_res = await heuristic_classify(t_low, user_id, context={**ctx, "profile": profile}, intent_map=i_map, norm_query=norm_t)
        if h_res and h_res.data.get("intent_type") == "LEARN_COMMAND": return h_res

        c_t, susp = await stt_corrector.correct(transcript, u_dict, norm_query=norm_t)
        # Elite V62.5 Bypass: Do NOT ask for confirm if intent is already explicit (Tạo sản phẩm / Viết bài)
        explicit_intent = any(kw in transcript.lower() for kw in ["tạo sản phẩm", "viết bài", "viết bài:", "tạo bài", "tao san pham", "viet bai"])
        if susp and not explicit_intent: 
            return await self._ask_stt_confirm(user_id, ctx, transcript, c_t, susp, profile, i_map)

        transcript = c_t
        h_res = await heuristic_classify(transcript.lower(), user_id, context={**ctx, "profile": profile}, intent_map=i_map, norm_query=norm_t)
        if h_res: return h_res

        # Semantic / Cloud
        try:
            s_int, s_score = await self.semantic_router.classify(transcript)
            if s_score >= 0.82 and s_int in INTENT_TO_ACTION:
                return await self._resolve_semantic(s_int, s_score, transcript)
        except: pass

        res = await self.t2_router.extract(transcript, context=context, screen_context=screen_context)
        if res and res.status == "success":
            ctx.update({"last_target": res.data.get("target"), "last_timeframe": res.data.get("timeframe")})
            await xohi_memory.set_user_context(user_id, ctx)
        return res or IntentResponse(status="success", action=IntentAction.ANALYZE, message="", router_tier=RouterTier.TIER_3_REASONING, data={"intent_type": "UNKNOWN", "cleaned_transcript": transcript})

    def _match(self, triggers, norm, pho) -> bool:
        for t in triggers:
            tn = normalize_vn(t.lower()); tp = tn.replace("k", "c").replace("q", "c")
            if tn in norm or tp in pho or fuzz.ratio(pho, tp) > (80 if len(tn) <= 4 else 90): return True
        return False

    async def _strip_wake(self, raw: str, triggers: List[str]) -> Optional[str]:
        rem = raw; matched = False
        while True:
            loop = False; rn = normalize_vn(rem.lower())
            for t in triggers:
                tn = normalize_vn(t.lower())
                if rn.startswith(tn):
                    words = t.split(); split = rem.split(None, len(words))
                    rem = split[-1].strip(", ") if len(split) > len(words) else ""; loop = matched = True; break
            if not loop: break
        return rem if matched and rem else None

    async def _handle_wake(self, user_id: str, greeting: str) -> IntentResponse:
        from backend.services.xohi.creative_studio.orchestrator import content_factory
        async with async_session_maker() as s:
            repo = ContentCampaignRepository(session=s)
            active = await content_factory.get_active_campaign(repo, user_id=user_id)
            if active: return IntentResponse(status="success", action=IntentAction.READ, message=content_factory.format_resume_greeting(active), router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "CONTENT_CREATE", "action": "RESUME_ROUTINE", "campaign_id": active.id})
        return IntentResponse(status="success", action=IntentAction.READ, message=greeting, router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "WAKE_ROUTINE"})

    async def _handle_stt_confirm(self, uid, ctx, norm_t, u_dict, profile, i_map) -> IntentResponse:
        if any(kw in norm_t for kw in NORM_YES_KEYWORDS):
            syn = await intent_synapse.retrieve_and_clear(uid)
            if syn and syn.get("classification"):
                d = syn["classification"]; ctx["is_confirming_stt"] = False; await xohi_memory.set_user_context(uid, ctx)
                return IntentResponse(status="success", action=IntentAction(d.get("action", "READ")), message=d.get("message", ""), router_tier=RouterTier.TIER_1_HEURISTIC, data=d)
            susp = ctx.get("pending_stt_correction", {})
            if susp: u_dict.update(susp); await stt_corrector.smart_learn(uid, list(susp.keys())[0], list(susp.values())[0])
            ctx["is_confirming_stt"] = False; await xohi_memory.set_user_context(uid, ctx)
            t = ctx.get("pending_cleaned_transcript", "")
            return await heuristic_classify(t.lower(), uid, context={**ctx, "profile": profile}, intent_map=i_map, norm_query=normalize_vn(t))
        ctx["is_confirming_stt"] = False; await xohi_memory.set_user_context(uid, ctx)
        return IntentResponse(status="error", action=IntentAction.READ, message="Dạ vâng, sếp nói lại giúp em.")

    async def _ask_stt_confirm(self, uid, ctx, raw, clean, susp, profile, i_map) -> IntentResponse:
        ctx.update({"is_confirming_stt": True, "pending_stt_correction": susp, "pending_cleaned_transcript": clean})
        await xohi_memory.set_user_context(uid, ctx)
        vt = clean
        for w, r in susp.items(): vt = re.sub(re.escape(w), r, vt, flags=re.IGNORECASE)
        shadow = await heuristic_classify(vt.lower(), uid, context={**ctx, "profile": profile}, intent_map=i_map, norm_query=normalize_vn(vt))
        d = shadow.data if shadow else {"intent_type": "UNKNOWN"}
        d.update({"cleaned_transcript": vt, "source_tag": "shadow"})
        await intent_synapse.store_pending_intent(uid, d, vt)
        return IntentResponse(status="success", action=IntentAction.READ, message=f"Dạ, có phải ý sếp là '{list(susp.values())[0]}' không ạ?", router_tier=RouterTier.TIER_1_HEURISTIC, data={"intent_type": "SESSION_CTRL", "action": "STT_CONFIRM"})

    async def _resolve_semantic(self, s_int, s_score, t) -> IntentResponse:
        m = INTENT_TO_ACTION[s_int]
        return IntentResponse(status="success", action=IntentAction(m.get("action", "READ")), message=m.get("message", ""), router_tier=RouterTier.TIER_1_HEURISTIC, data={**m, "semantic_score": s_score, "cleaned_transcript": t})
