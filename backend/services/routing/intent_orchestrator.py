import logging, os, asyncio, json, time, unicodedata, re
from rapidfuzz import fuzz
from typing import List, Dict, Optional, Tuple, Union, TypedDict, TYPE_CHECKING, cast

from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from .tier2_cloud import Tier2CloudRouter
from .tier3_cloud import Tier3CloudRouter
from .tier2_refiner import Tier2Refiner
from .stt_corrector import stt_corrector
from backend.services.data_injector import data_injector
from backend.services.ai_engine.core.semantic_router import SemanticRouter, INTENT_TO_ACTION
from backend.services.xohi_memory import xohi_memory
from backend.utils.text import normalize_vn, sanitize_id
from .heuristic_classifier import heuristic_classify
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.alchemy_config import alchemy_config

if TYPE_CHECKING:
    from backend.database.models import ContentCampaign

from backend.services.ai_engine.core.vector_memory import VectorMemory
from .intent_synapse import intent_synapse

# Pre-compiled regex for STT confirmed word boundaries
STT_CONFIRM_RE_CACHE: Dict[str, re.Pattern] = {}

# --- Global Keywords & Mappings (R1.6: Zero-Hydration Constants) ---
YES_KEYWORDS = ["đúng", "vâng", "yes", "ừ", "ok", "ok đi", "chuẩn", "đươc", "rồi", "chính xác", "phải", "phai", "có"]
NO_KEYWORDS = ["không", "nhầm", "sai", "no"]
NAV_KEYWORDS = ["mở", "xem", "vào", "biểu đồ", "show", "open", "display", "chart", "bi do", "bí đồ"]

# Phase 76.3: Pre-normalized versions for O(1) or fast O(N) lookup
NORM_YES_KEYWORDS = {normalize_vn(kw) for kw in YES_KEYWORDS}
NORM_NO_KEYWORDS = {normalize_vn(kw) for kw in NO_KEYWORDS}
NORM_NAV_KEYWORDS = {normalize_vn(kw) for kw in NAV_KEYWORDS}

WAKE_TRIGGERS = ["xohi", "so hi", "xo hi", "số hi", "xố hỉ", "số hỉ", "so huy", "số huy", "chao", "xin chao"]
SLEEP_TRIGGERS = ["cut", "ngu di", "thoat", "tam biet", "bye"]
NORM_WAKE_TRIGGERS = [normalize_vn(kw) for kw in WAKE_TRIGGERS]
NORM_SLEEP_TRIGGERS = [normalize_vn(kw) for kw in SLEEP_TRIGGERS]

TIMEFRAME_VI_MAP = {
    "today": "hôm nay",
    "this_month": "tháng này",
    "this_week": "tuần này",
    "yesterday": "hôm qua",
    "last_month": "tháng trước",
    "none": ""
}

TARGET_VI_MAP = {
    "revenue": "doanh số",
    "order": "số đơn hàng",
    "product": "số sản phẩm",
    "user": "số khách hàng"
}

NAV_MSG_MAP = {
    "revenue":  "biểu đồ doanh thu",
    "order":    "quản lý đơn hàng",
    "product":  "quản lý sản phẩm",
    "user":     "danh sách nhân viên",
    "category": "quản lý danh mục",
    "news":     "quản lý bài viết",
    "settings": "cài đặt giọng nói"
}
# -------------------------------------------------------------------

# Pre-created session maker for proactive resume checks (V76)
async_session_maker = alchemy_config.create_session_maker()

# --- Phase 76.3: Trigger Optimization Cache ---
TRIGGER_PHO_CACHE = {} # { "word": "word_pho" }
TRIGGER_NORM_CACHE = {} # { "word": "word_norm" }

def _get_norm_trigger(word: str) -> str:
    if word not in TRIGGER_NORM_CACHE:
        TRIGGER_NORM_CACHE[word] = normalize_vn(word)
    return TRIGGER_NORM_CACHE[word]

def _get_phonetic(word: str) -> str:
    if word not in TRIGGER_PHO_CACHE:
        TRIGGER_PHO_CACHE[word] = word.replace("k", "c").replace("q", "c")
    return TRIGGER_PHO_CACHE[word]

def _match_trigger(words_list: List[str], trans_norm: str, trans_pho: Optional[str] = None) -> bool:
    if not words_list: return False

    # 76.3: Use pre-calculated phonetic transcript if provided
    if trans_pho is None:
        trans_pho = trans_norm.replace("k", "c").replace("q", "c")

    for w in words_list:
        # 76.3: Use cached normalization and phonetic mapping
        w_norm = _get_norm_trigger(w)
        w_pho = _get_phonetic(w_norm)

        if w_norm in trans_norm or w_pho in trans_pho:
            return True

        # For very short triggers (like "cut", "xohi"), be more lenient on the ratio
        threshold = 80 if len(w_norm) <= 4 else 90
        if fuzz.ratio(trans_pho, w_pho) > threshold:
            return True
    return False

class AppState(TypedDict, total=False):
    is_confirming_stt: bool
    pending_stt_correction: Dict[str, str]
    pending_cleaned_transcript: str
    pending_raw_transcript: str
    last_target: Optional[str]
    last_timeframe: Optional[str]
    last_semantic_results: Optional[str]
    stt_dictionary: Dict[str, str]

class ContextItem(TypedDict):
    role: str
    content: str


class RouterOrchestrator:
    """
    C.O.R.E ARCHITECTURE — Central Orchestrated Routing Engine
    ============================================================
    T1 (Local, 0ms) → T2 (Dispatcher) → Trinity Loop (Inject + Refine).
    """
    def __init__(self):
        self.semantic_router = SemanticRouter()  # T1.5: Embedding-based classify
        self.t2_router = Tier2CloudRouter()
        self.t3_router = Tier3CloudRouter()
        self.t2_refiner = Tier2Refiner()

    async def _get_rag_context(self, transcript: str) -> str:
        """Phase 76.4: Unified RAG Context Fetcher."""
        try:
            lower_t = transcript.lower()
            if any(kw in lower_t for kw in ["sản phẩm", "hàng", "tồn kho", "giá", "mặt hàng", "product"]):
                return await VectorMemory.search(transcript, session=None, context_type="product", limit=3)
            elif any(kw in lower_t for kw in ["bài viết", "tin tức", "chính sách", "hướng dẫn", "article", "news"]):
                return await VectorMemory.search(transcript, session=None, context_type="article", limit=3)
        except Exception as e:
            logger.debug(f"[RAG] Vector search skipped: {e}")
        return ""

    async def classify(
        self,
        transcript: str,
        user_id: str,
        app_state: AppState,
        context: Optional[List[ContextItem]] = None,
        screen_context: Optional[Dict[str, object]] = None,

        modality: str = "text"
    ) -> IntentResponse:
        """Phase 1: Intent Resolution (T1 -> T2 Dispatch)"""
        t0 = time.monotonic()
        user_id = sanitize_id(user_id) or "default"
        m_tag = "v" if modality == "voice" else "c"
        transcript = unicodedata.normalize('NFC', transcript.strip())
        logger.info(f"--- [C.O.R.E][{m_tag}] Raw Transcript: '{transcript}' ---")

        # 76.3.1: FAST-PATH FOR SYSTEM COMMANDS (0ms)
        # Nhận diện lệnh hệ thống NGAY LẬP TỨC trước khi gọi bất kỳ STT AI hay Memory nào.
        transcript_lower = transcript.lower()
        normalized_transcript = normalize_vn(transcript_lower)
        trans_pho = normalized_transcript.replace("k", "c").replace("q", "c")

        # Check persistent context from xohi_memory

        # Phase 76.3: Atomic Aggregation (Rule R82.25)
        orchestrator_ctx: Dict[str, object] = await xohi_memory.get_full_orchestrator_context(user_id)
        user_profile: Dict[str, object] = cast(Dict[str, object], orchestrator_ctx.get("profile", {}))
        ctx: Dict[str, object] = cast(Dict[str, object], orchestrator_ctx.get("ctx", {}))
        user_dict: Dict[str, str] = cast(Dict[str, str], orchestrator_ctx.get("stt", {}))
        intent_map: Dict[str, List[str]] = cast(Dict[str, List[str]], orchestrator_ctx.get("intent_map", {}))

        # --- PHASE 0.5: NEURAL WAKE TRIGGERS (CTO V1.9) ---
        DEFAULT_GREETING = user_profile.get("greeting_template", "Dạ, em nghe đây sếp.")
        wake_words = user_profile.get("wake_words", [])
        sleep_words = user_profile.get("sleep_words", [])
        
        # Quick STT Dict bypass for Wake/Sleep (0ms)
        # 76.3: Reuse transcript_lower from fast-path
        if user_dict:
            applied_correction = False
            for wrong, right in user_dict.items():
                if wrong in transcript_lower:
                    transcript_lower = transcript_lower.replace(wrong, right)
                    applied_correction = True

            if applied_correction:
                normalized_transcript = normalize_vn(transcript_lower)
                trans_pho = normalized_transcript.replace("k", "c").replace("q", "c")

        # 0.5.1: Heuristic High-Speed Match (0ms)
        # 76.3: Pre-calculate phonetic version once
        trans_pho = normalized_transcript.replace("k", "c").replace("q", "c")

        # 76.3: Use pre-normalized triggers from module constants
        is_wake = _match_trigger(wake_words + NORM_WAKE_TRIGGERS, normalized_transcript, trans_pho=trans_pho)
        is_sleep = _match_trigger(sleep_words + NORM_SLEEP_TRIGGERS, normalized_transcript, trans_pho=trans_pho)

        # 0.5.2: Semantic Fallback (Neural Trigger)
        if not is_wake and not is_sleep:
            # Check semantically if the intent is wake/sleep even if words don't match exactly
            sem_intent, sem_score = await self.semantic_router.classify(
                transcript,
                extra_intents={
                    "session_wake_user": wake_words,
                    "session_sleep_user": sleep_words
                }
            )
            if sem_score > 0.85:
                if sem_intent == "session_wake_user": is_wake = True
                if sem_intent == "session_sleep_user": is_sleep = True
                logger.debug(f"[T1.5 Neural Wake] MATCHED via semantics: {sem_intent} (score={sem_score:.2f})")

        if is_wake:
            # Phase 77.4: Check for continuation (Significant Content Policy)
            # If the user said "XoHi, do X", we strip "XoHi" and continue to Tier 1.1
            remaining_transcript = transcript
            matched_any = False
            
            # Recursive stripping of wake words (Case: "Chào XoHi, ...")
            while True:
                stripped_in_loop = False
                rem_lower = remaining_transcript.lower()
                rem_norm = normalize_vn(rem_lower)
                
                for w in (wake_words + WAKE_TRIGGERS):
                    w_norm = normalize_vn(w.lower())
                    if rem_norm.startswith(w_norm):
                        # Find the actual length in the raw string to slice correctly
                        # Use a simple space-based word count or just find the end of the first word
                        # But wake words can be multi-word (e.g. "xin chao")
                        # A safer way: since we know it starts with w_norm, we find how many chars of 
                        # remaining_transcript map to that w_norm.
                        # For now, a practical heuristic: split by space and check words
                        w_words = w.split()
                        raw_split = remaining_transcript.split(None, len(w_words))
                        if len(raw_split) >= len(w_words):
                            # Ensure the first N words actually match the wake word semantically
                            # (already guaranteed by startswith check on norm)
                            remaining_transcript = raw_split[-1] if len(raw_split) > len(w_words) else ""
                            remaining_transcript = remaining_transcript.strip(", ").strip()
                            stripped_in_loop = True
                            matched_any = True
                            break
                if not stripped_in_loop:
                    break

            if matched_any and remaining_transcript:
                logger.debug(f"[T1 Wake] Continuation detected. Stripping wake(s) and proceeding: '{remaining_transcript}'")
                transcript = remaining_transcript
                # Reset normalization for the cleaned transcript
                transcript_lower = transcript.lower()
                normalized_transcript = normalize_vn(transcript_lower)
                # Proceed to Tier 1.1 below
            elif matched_any and not remaining_transcript:
                # Standalone wake - proceed to proactive resume logic exactly once
                pass 
            
            if not remaining_transcript:
                # 0.5.3: Proactive Resume Check (Rule R81)
                # If sếp just wakes XoHi, check if there's an active campaign to report
                try:
                    from backend.database.models import ContentCampaign
                    async with async_session_maker() as session:
                        active = await content_factory.get_active_campaign(session, user_id=user_id)
                        if active:
                            resume_msg = content_factory.format_resume_greeting(active)
                            logger.info(f"[Proactive Resume] Found active campaign {active.id}, hijacking greeting.")
                            return IntentResponse(
                                status="success", action=IntentAction.READ,
                                message=resume_msg,
                                router_tier=RouterTier.TIER_1_HEURISTIC,
                                data={
                                    "category": "CONTENT_CREATE",
                                    "action": "RESUME_ROUTINE",
                                    "campaign_id": active.id,
                                    "step": active.current_step,
                                    "status": active.status
                                },
                                cost_tokens=0.0
                            )
                except Exception as e:
                    logger.warning(f"[Proactive Resume] Check failed: {e}")

                return IntentResponse(status="success", action=IntentAction.READ, message=DEFAULT_GREETING, router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "WAKE_ROUTINE", "confidence": 1.0}, cost_tokens=0.0)
        
        is_sleep = _match_trigger(NORM_SLEEP_TRIGGERS, normalized_transcript, trans_pho=trans_pho)
        if is_sleep:
            # Stricter standalone check for sleep
            if len(transcript.split()) <= 2:
                return IntentResponse(status="success", action=IntentAction.READ, message="Hẹn gặp lại sếp.", router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "HARDWARE_SLEEP", "confidence": 1.0}, cost_tokens=0.0)

        # --- PHASE 1: INTERACTIVE STT LEARNING (MOLBOOK STYLE) ---
        if ctx.get("is_confirming_stt"):
            # Phase 76.3: Use pre-normalized transcript for confirmation check
            is_yes = any(kw in normalized_transcript for kw in NORM_YES_KEYWORDS)
            is_no = any(kw in normalized_transcript for kw in NORM_NO_KEYWORDS)

            if is_yes and not is_no:
                # ════════════════════════════════════════════════════════════════════
                # VIRAL 2026: RECURRENT INTENT PROPAGATION (RIP)
                # ════════════════════════════════════════════════════════════════════
                synapse = await intent_synapse.retrieve_and_clear(user_id)
                if synapse:
                    logger.info(f"[Neural Synapse] RESTORING sequence with stored intent data: '{synapse['query']}'")
                    # VIRAL 2026: Direct Return of stored classification to bypass re-correction loops
                    stored_data = synapse.get("classification")
                    if stored_data:
                        # Convert back to IntentResponse
                        action_str = stored_data.get("action", "READ")
                        action = IntentAction(action_str) if isinstance(action_str, str) else action_str
                        
                        # Clear confirmation state
                        ctx["is_confirming_stt"] = False
                        ctx["pending_stt_correction"] = {}
                        await xohi_memory.set_user_context(user_id, ctx)
                        
                        return IntentResponse(
                            status="success",
                            action=action,
                            message=stored_data.get("message", ""),
                            router_tier=RouterTier.TIER_1_HEURISTIC,
                            cost_tokens=0.0,
                            data=stored_data
                        )
                else:
                    # User confirmed! Save to memory
                    suspected = ctx.get("pending_stt_correction", {})
                    if suspected:
                        user_dict.update(suspected)
                        ctx["stt_dictionary"] = user_dict

                        # Persist to Redis (permanent)
                        for wrong, right in suspected.items():
                            await stt_corrector.smart_learn(user_id, wrong, right)
                    
                    # Restore the cleaned transcript
                    transcript = ctx.get("pending_cleaned_transcript", "").strip()
                    logger.info(f"[STT Learning] Resuming execution with corrected transcript: '{transcript}'")
                    normalized_transcript = normalize_vn(transcript)

                # Clear state
                ctx["is_confirming_stt"] = False
                ctx["pending_stt_correction"] = {}
                await xohi_memory.set_user_context(user_id, ctx)
                
            elif is_no:
                ctx["is_confirming_stt"] = False
                ctx["pending_stt_correction"] = {}
                await xohi_memory.set_user_context(user_id, ctx)
                return self._error_response("Dạ vâng, sếp nói lại yêu cầu giúp em nhé.")
            else:
                # If they didn't say YES or NO clearly, assume they are asking something else
                ctx["is_confirming_stt"] = False
                ctx["pending_stt_correction"] = {}
                await xohi_memory.set_user_context(user_id, ctx)
                # Fall through to normal classification
        else:
            # 0. AI STT Correction
            
            # --- PHASE 0.9: RAW HEURISTIC GUARD (V77.6) ---
            # Check for high-priority learning commands on RAW transcript before AI "cleans" it.
            # This prevents AI from thinking "hoc lenh" is noise and stripping it.
            raw_heur = await self._heuristic_classify(
                transcript.lower(), 
                user_id, 
                ctx={**ctx, "profile": user_profile}, 
                intent_map=intent_map, 
                norm_query=normalized_transcript
            )
            if raw_heur and raw_heur.data.get("intent_type") == "LEARN_COMMAND":
                logger.info(f"[Raw Heuristic Guard] HIT: LEARN_COMMAND")
                t_heur = int((time.monotonic() - t0) * 1000)
                raw_heur.data["cleaned_transcript"] = transcript
                return raw_heur

            # --- SEMANTIC BYPASS (LOCAL-FIRST) ---
            cleaned_transcript, suspected = await stt_corrector.correct(transcript, user_dict, norm_query=normalized_transcript)
            t_stt = int((time.monotonic() - t0) * 1000)
            logger.info(f"--- [C.O.R.E][{m_tag}] Corrected: '{transcript}' -> '{cleaned_transcript}' ({t_stt}ms) ---")
            
            # If the transcript was cleaned locally or by AI, and it's 100% clear (no suspect),
            # we should immediately try T1 Semantic Router and Heuristics BEFORE T2 LLM.
            if not suspected:
                # Phase 76.4: Inherit context-aware classification
                heur_res = await self._heuristic_classify(
                    cleaned_transcript.lower(),
                    user_id,
                    ctx={**ctx, "profile": user_profile}, # Pass context with profile
                    intent_map=intent_map,
                    norm_query=normalized_transcript
                )
                if heur_res:
                    if heur_res.data is None:
                        heur_res.data = {}
                    heur_res.data["cleaned_transcript"] = cleaned_transcript

                    # Phase 76.4: Proactive RAG for Heuristic Bypass
                    if heur_res.data.get("intent_type") == "DATA_QUERY":
                        rag_res = await self._get_rag_context(cleaned_transcript)
                        if rag_res:
                            heur_res.semantic_results = rag_res
                            logger.info(f"[Heuristic RAG] Injected semantic results")

                    # Update Redis context for continuity
                    ctx["last_target"] = heur_res.data.get("target")
                    ctx["last_timeframe"] = heur_res.data.get("timeframe")
                    await xohi_memory.set_user_context(user_id, ctx)

                    t_heur = int((time.monotonic() - t0) * 1000)
                    logger.info(f"[Heuristic Bypass] Classified in {t_heur}ms: {heur_res.data.get('intent_type')} target={heur_res.data.get('target')}")
                    return heur_res
            
            # Restore original flow for suspected/ambiguous ones
            if suspected:
                # Intercept! Ask for confirmation
                ctx["is_confirming_stt"] = True
                ctx["pending_stt_correction"] = suspected
                ctx["pending_cleaned_transcript"] = cleaned_transcript
                ctx["pending_raw_transcript"] = transcript # Phase 77: Save for learning loop
                await xohi_memory.set_user_context(user_id, ctx)
                
                # Format a friendly confirmation message
                wrong_word = list(suspected.keys())[0]
                right_word = suspected[wrong_word]
                
                msg = f"Dạ, có phải ý sếp là '{right_word}' không ạ?"
                
                # VIRAL 2026: Calculate Neural Shadow Intent (What the user actually meant)
                # Apply correction for the VIRTUAL intent calculation
                virtual_transcript = cleaned_transcript
                for w, r in suspected.items():
                    virtual_transcript = re.sub(re.escape(w), r, virtual_transcript, flags=re.IGNORECASE)
                
                # Classify the shadow intent BEFORE storing in synapse
                shadow_res = await self._heuristic_classify(
                    virtual_transcript.lower(),
                    user_id,
                    ctx={**ctx, "profile": user_profile},
                    intent_map=intent_map,
                    norm_query=normalize_vn(virtual_transcript)
                )
                
                pending_data: Dict[str, object] = shadow_res.data if shadow_res else {"intent_type": "UNKNOWN"}
                # Add source tag for logging
                pending_data["source_tag"] = "shadow"
                
                # Store the ACTUAL intent data in synapse (Recurrent Intent Propagation)
                await intent_synapse.store_pending_intent(user_id, pending_data, virtual_transcript)

                return IntentResponse(
                    status="success",
                    action=IntentAction.READ,
                    message=msg,
                    router_tier=RouterTier.TIER_1_HEURISTIC,
                    cost_tokens=0.0,
                    data={"intent_type": "SESSION_CTRL", "action": "STT_CONFIRM", "suspected_correction": right_word}
                )
            
            # Update transcript for the rest of the flow
            transcript = cleaned_transcript        
        
        combined_lower = transcript.lower()
        # 1.1 TIER 1.1: Heuristic Fallback (Zen Path, 0-Token, <1ms)
        # Classify straightforward patterns / learned commands BEFORE fuzzy semantics
        # Phase 76.4: Pass session maker for content factory checks if needed
        result = await self._heuristic_classify(combined_lower, user_id, ctx={**ctx, "profile": user_profile}, intent_map=intent_map, norm_query=normalized_transcript)
        if result:
            logger.info(f"[Heuristic Priority] HIT: {result.data.get('intent_type')}")
            # Update last context
            ctx["last_target"] = result.data.get("target")
            ctx["last_timeframe"] = result.data.get("timeframe")
            await xohi_memory.set_user_context(user_id, ctx)
            return result

        # 1.5 TIER 1.5: Embedding Semantic Classify (~50ms, 0-Token)
        try:
            sem_intent, sem_score = await self.semantic_router.classify(transcript)
            logger.debug(f"[T1.5] Semantic: '{transcript}' → {sem_intent} ({sem_score:.3f})")
            
            # Increased threshold to 0.82 to avoid English short phrases from triggering VN embeddings
            if sem_score >= 0.82 and sem_intent in INTENT_TO_ACTION:
                mapping = INTENT_TO_ACTION[sem_intent]
                action_map = {"COUNT": IntentAction.COUNT, "READ": IntentAction.READ,
                              "MUTATE": IntentAction.MUTATE, "ANALYZE": IntentAction.ANALYZE,
                              "CONTENT_CREATE": IntentAction.CONTENT_CREATE,
                "CONTENT_APPROVE": IntentAction.CONTENT_APPROVE,
                "CONTENT_REJECT": IntentAction.CONTENT_REJECT,
                "WAKE_ROUTINE": IntentAction.WAKE_ROUTINE,
                "HARDWARE_SLEEP": IntentAction.HARDWARE_SLEEP}
                
                # If action gives us HARDWARE_SLEEP, bypass the regular enum mapping
                # and put it directly into the data payload to trigger the frontend event, 
                # but keep the intent enum as READ to pass Pydantic validation.
                action_str = mapping.get("action", "READ")
                
                # CTO Fix: Only trigger HARDWARE_SLEEP if the intent type is explicitly SESSION_CTRL 
                if action_str == "HARDWARE_SLEEP" and mapping.get("intent_type") != "SESSION_CTRL":
                    action_str = "READ"

                action = action_map.get(action_str, IntentAction.READ)
                msg_val = mapping.get("message", "")
                
                # Phase 76.4: Proactive Semantic Result Injection
                semantic_results = ""
                if sem_intent == "product_query":
                    semantic_results = await self._get_rag_context(transcript)

                logger.info(f"[T1.5] HIT (score={sem_score:.3f}): {sem_intent} → {mapping['intent_type']}")
                return IntentResponse(
                    status="success",
                    action=action,
                    message=msg_val,
                    router_tier=RouterTier.TIER_1_HEURISTIC,
                    cost_tokens=0.0,
                    semantic_results=semantic_results or None,
                    data={
                        "intent_type": mapping["intent_type"],
                        "target": mapping.get("target", "none"),
                        "timeframe": "none",
                        "ui_action": action_str if action_str == "HARDWARE_SLEEP" else mapping.get("ui_action", ""),
                        "widget_id": mapping.get("ui_action", ""),
                        "semantic_score": sem_score,
                        "cleaned_transcript": transcript,
                        **({"category": mapping["category"]} if "category" in mapping else {}),
                    }
                )
        except Exception as e:
            logger.warning(f"[T1.5] SemanticRouter error (non-fatal): {e}")

        # 2. TIER 2: Central Dispatcher (Flash)
        result = None
        try:
            result = await self.t2_router.extract(transcript, context=context, screen_context=screen_context)
        except Exception as e:
            logger.error(f"[T2] Dispatch Failure: {e}")

        # Update persistent context for VUI Continuity (Phase 76.4)
        if result and result.status == "success":
            ctx["last_target"] = result.data.get("target")
            ctx["last_timeframe"] = result.data.get("timeframe")
            if result.semantic_results:
                ctx["last_semantic_results"] = result.semantic_results
            await xohi_memory.set_user_context(user_id, ctx)

        # Phase 77: Hardening — Fallback to Tier 3 Reasoning instead of error
        if not result:
            logger.info(f"[C.O.R.E][{m_tag}] Classification inconclusive -> Defaulting to Tier 3 Reasoning")
            return IntentResponse(
                status="success",
                action=IntentAction.ANALYZE,
                message="",
                router_tier=RouterTier.TIER_3_REASONING,
                data={"intent_type": "UNKNOWN", "cleaned_transcript": transcript},
                cost_tokens=0.0
            )

        if result and result.data is None:
            result.data = {}
        result.data["cleaned_transcript"] = transcript
        
        intent_data = result.data
        intent_type = intent_data.get("intent_type", "UNKNOWN")

        # Phase 76.4: Proactive RAG for Tier 2 Cloud Results
        if intent_type in ["DATA_QUERY", "PRODUCT_INFO"] and not result.semantic_results:
            lower_t = transcript.lower()
            if any(kw in lower_t for kw in ["sản phẩm", "hàng", "giá", "tồn kho"]):
                rag_res = await self._get_rag_context(transcript)
                if rag_res:
                    result.semantic_results = rag_res
                    logger.info(f"[T2 RAG] Injected semantic results for {intent_type}")

        # ══════════════════════════════════════════════════════════════════════════
        # Rule R82.25: Global UI Action Enforcer (Decouple Query from Navigation)
        # ══════════════════════════════════════════════════════════════════════════
        if intent_type == "DATA_QUERY" or result.action == IntentAction.COUNT:
            # Check for explicit navigation intent in transcript
            has_nav_target = any(kw in transcript.lower() for kw in NAV_KEYWORDS)

            if not has_nav_target and (result.data.get("ui_action") or result.data.get("widget_id")):
                logger.debug(f"[CORE][Filter] Stripping unsolicited UI action '{result.data.get('ui_action')}' from DATA_QUERY")
                result.data["ui_action"] = ""
                result.data["widget_id"] = ""
        # ══════════════════════════════════════════════════════════════════════════

        if intent_type == "UNKNOWN":
            # Route to T3 with hardened Absolute Boundary prompt for polite rejection
            logger.debug(f"[C.O.R.E][{m_tag}] UNKNOWN intent → Routing to T3 for boundary-aware response")
            return result

        if result and result.data is not None:
            result.data["effective_transcript"] = transcript
            logger.info(f"[C.O.R.E] Final: msg='{result.message[:50]}...' type={result.data.get('intent_type')} ui={result.data.get('ui_action')}")
        return result

    async def execute(
        self,
        classification: IntentResponse,
        transcript: str,
        db_session: AsyncSession,
        context: Optional[List[Dict[str, object]]] = None,
        screen_context: Optional[Dict[str, object]] = None,
        user_id: Optional[str] = None,
        modality: str = "text"
    ) -> IntentResponse:
        """Phase 2: Action Execution (Phase 3 of Trinity Loop)"""
        start_time = time.monotonic()
        intent_data = classification.data or {}

        # VERY IMPORTANT: Use the cleaned transcript from classification payload to prevent STT hallucinations down the pipeline
        transcript = intent_data.get("cleaned_transcript", transcript)

        intent_type = intent_data.get("intent_type", "UNKNOWN")

        # 1. RÚT ACTION AN TOÀN CHỐNG CRASH
        class_action_str = classification.action.value if hasattr(classification.action, "value") else str(classification.action)
        m_tag = "v" if modality == "voice" else "c"

        if intent_type == "LEARN_COMMAND":
            logger.info(f"[C.O.R.E][{m_tag}] Learning new command: '{intent_data.get('learn_keyword')}' -> '{intent_data.get('learn_target')}'")
            # Phase 77.1: Normalize keyword to ensure Zen Path hit
            learn_kw = normalize_vn(intent_data.get("learn_keyword", "").lower())
            learn_tgt = intent_data.get("learn_target")

            if learn_kw and learn_tgt:
                # Target to Widget Map (Phase 77.1: Dynamic & Session Resolution)
                target_map = {
                    "chiến dịch": "show_campaigns", "campaign": "show_campaigns", "camp": "show_campaigns",
                    "chương dịch": "show_campaigns", "cam": "show_campaigns",
                    "đơn hàng": "show_order_management", "order": "show_order_management",
                    "sản phẩm": "show_product_management", "product": "show_product_management",
                    "nhân viên": "show_user_management", "user": "show_user_management", "khách hàng": "show_user_management",
                    "danh mục": "show_category_management", "category": "show_category_management",
                    "doanh thu": "show_revenue_chart", "revenue": "show_revenue_chart", "tiền": "show_revenue_chart",
                    "tin tức": "show_news_management", "news": "show_news_management", "bài viết": "show_news_management",
                    "cài đặt": "show_voice_settings", "settings": "show_voice_settings",
                    # Phase 77.1: Session & Identity Aliases
                    "tạm biệt": "HARDWARE_SLEEP", "đi ngủ": "HARDWARE_SLEEP", "ngủ": "HARDWARE_SLEEP", "cút": "HARDWARE_SLEEP",
                    "lời chào": "WAKE_ROUTINE", "chào": "WAKE_ROUTINE", "mày là ai": "WAKE_ROUTINE", "identity": "WAKE_ROUTINE"
                }

                resolved_widget = target_map.get(learn_tgt.lower(), learn_tgt)

                # Persist to Redis
                current_map = await xohi_memory.get_system_intent_mapping()
                is_update = learn_kw in current_map
                current_map[learn_kw] = resolved_widget
                await xohi_memory.set_system_intent_mapping(current_map)

                verb = "cập nhật" if is_update else "ghi nhớ"
                msg = f"Dạ sếp, em đã {verb} lệnh mới. Từ nay mỗi khi sếp bảo '{learn_kw}' thì em sẽ mở '{learn_tgt}' ngay ở Tier 1 (Zen Path) ạ!"
                return IntentResponse(
                    status="success",
                    action=IntentAction.READ,
                    message=msg,
                    router_tier=RouterTier.TIER_1_HEURISTIC,
                    cost_tokens=classification.cost_tokens,
                    data={"intent_type": "LEARN_SUCCESS", "keyword": learn_kw, "widget": resolved_widget, "is_update": is_update}
                )
            return self._error_response("Dạ sếp, em chưa nghe rõ sếp muốn dạy gì ạ.")

        if intent_type == "DEEP_ANALYSIS" or intent_type == "UNKNOWN" or class_action_str == "ANALYZE":
            logger.debug(f"[C.O.R.E][{m_tag}] Executing T3 Reasoning (intent_type={intent_type})")

            # RAG: Inject vector search context for grounded reasoning
            rag_context = await self._get_rag_context(transcript)

            # Append RAG to transcript for T3
            enriched_transcript = transcript
            if rag_context and rag_context not in ["", "Hệ thống tri thức đang khởi động, sếp đợi em chút ạ."]:
                enriched_transcript = f"{transcript}\n\n[DỮ LIỆU THAM KHẢO TỪ HỆ THỐNG]\n{rag_context}"
                logger.info(f"[RAG] Injected {len(rag_context)} chars of context into T3")

            return await self.t3_router.reason(enriched_transcript, context, screen_context=screen_context)

        # ══════════════════════════════════════════
        # V62.1: CONTENT_CREATE → Content Factory Pipeline
        # ══════════════════════════════════════════
        if intent_type == "CONTENT_CREATE" or class_action_str == "CONTENT_CREATE":
            logger.info(f"[C.O.R.E][{m_tag}] Delegating to Content Factory V62.1.")
            # R106: Explicit session propagation (Elite V2.2)
            return await content_factory.handle_voice_request(
                transcript,
                session=db_session,
                user_id=user_id, # Rule R86: Propagate identity
                intent_data=intent_data
            )

        if intent_type == "CONTENT_APPROVE" or class_action_str == "CONTENT_APPROVE":
            logger.info(f"[C.O.R.E][{m_tag}] Approving Content Campaign...")
            latest = await content_factory.get_active_campaign(db_session, user_id=user_id)
            if latest:
                return await content_factory.approve_step(latest.id, {"approved": True, "step": latest.current_step}, db_session)
            return self._error_response("Dạ sếp muốn duyệt gì ạ? Hiện tại em chưa thấy có yêu cầu nào đang chờ duyệt.")

        if intent_type == "CONTENT_REJECT" or class_action_str == "CONTENT_REJECT":
            logger.info(f"[C.O.R.E][{m_tag}] Retrying/Rejecting Content Campaign...")
            latest = await content_factory.get_active_campaign(db_session, user_id=user_id)
            if latest:
                return await content_factory.retry_step(latest.id, db_session)
            return self._error_response("Dạ sếp muốn tạo lại gì ạ? Hiện tại em chưa thấy có bài viết nào đang dở.")

        # ══════════════════════════════════════════

        # DEFAULT: UI_NAV / DATA_QUERY → Xử lý Hybrid Loop
        # ══════════════════════════════════════════
        logger.debug(f"[T2] {intent_type} → Passing to Data Injector")

        t2_response = await data_injector.inject(
            classification,
            transcript,
            db_session=db_session,
            user_id=user_id,
            modality=modality
        )

        # 2. KIỂM TRA ACTION AN TOÀN CỦA T2
        t2_action_str = t2_response.action.value if hasattr(t2_response.action, "value") else str(t2_response.action)

        # --- TRINITY LOOP (NLG REFINER) ---
        # Nếu là lệnh đếm số liệu, dùng Refiner để làm mượt câu chữ
        if intent_type == "DATA_QUERY" or t2_action_str == "COUNT":
            raw_data = t2_response.data.get("injected_count") or t2_response.data.get("raw_count")
            if raw_data is not None:
                target = t2_response.data.get("target", "")
                # --- FAST REFINER (ZERO-LLM OPTIMIZATION) ---
                # Parse ANY numeric format to avoid LLM Refiner trip
                numeric_val = None
                if isinstance(raw_data, (int, float)):
                    numeric_val = float(raw_data)
                elif isinstance(raw_data, str):
                    # Strip Vietnamese currency formatting: "50.000.000đ (Hôm qua: ...)" -> 50000000
                    clean = str(raw_data).split("(")[0].strip()
                    clean = clean.replace("đ", "").replace(".", "").replace(",", "").strip()
                    try:
                        numeric_val = float(clean)
                    except ValueError:
                        pass
                
                if numeric_val is not None:
                    timeframe_vi = TIMEFRAME_VI_MAP.get(t2_response.data.get("timeframe"), "này")
                    target_vi = TARGET_VI_MAP.get(target, target)

                    # Smart Vietnamese number formatting
                    if target == "revenue":
                        formatted_val = self._format_vn_currency(numeric_val)
                        unit = ""
                    else:
                        formatted_val = f"{int(numeric_val):,}".replace(",", ".")
                        unit = ""
                    
                    if timeframe_vi:
                        refined_msg = f"Dạ thưa sếp, {target_vi} {timeframe_vi} là {formatted_val}{unit} ạ."
                    else:
                        refined_msg = f"Dạ thưa sếp, tổng {target_vi} hiện tại là {formatted_val}{unit} ạ."
                    refine_cost = 0.0
                    t_fast = int((time.monotonic() - start_time) * 1000)
                    logger.info(f"[Fast Refiner] ⚡ Local Bypass HIT ({t_fast}ms): {refined_msg}")
                else:
                    logger.debug("[Trinity Loop] Enhancing raw data with NLG Refiner...")
                    refined_msg, refine_cost = await self.t2_refiner.refine(transcript, target, str(raw_data))
                
                t2_response.message = refined_msg
                # CỘNG DỒN CHI PHÍ TOKEN CỦA REFINER
                t2_response.cost_tokens = (t2_response.cost_tokens or 0) + refine_cost
        
        elif intent_type == "UI_NAV" and not t2_response.message:
            # Default friendly message for T2 navigation if empty
            target = t2_response.data.get("target", "none")
            target_vi = NAV_MSG_MAP.get(target, "trang quản trị")
            t2_response.message = f"Dạ sếp, em mở {target_vi} cho sếp ngay đây ạ."

        # --- LOG MODALITY BRACKETING (XOHI[tag] for UI) ---
        # We modify the router_tier string to include the modality prefix
        if result and result.data is not None:
            # Rule R1.5: Secure type propagation
            res_data = cast(Dict[str, object], result.data)
            res_data["source_tag"] = m_tag
            res_data["router_tier_label"] = f"t{raw_tier}"
                
        logger.debug(f"[Trinity Loop] Final Msg: {t2_response.message} (Cost: {t2_response.cost_tokens} tokens)")

        duration = int((time.monotonic() - start_time) * 1000)
        logger.debug(f"[C.O.R.E][{m_tag}] Trinity Loop Complete in {duration}ms")
        return t2_response

    def _format_vn_currency(self, amount: float) -> str:
        """Format a number into natural Vietnamese currency (e.g., 50000000 -> 'gần 50 triệu đồng')."""
        if amount <= 0:
            return "0 đồng"
        if amount >= 1_000_000_000:
            val = amount / 1_000_000_000
            if val == int(val):
                return f"{int(val)} tỷ đồng"
            return f"khoảng {val:.1f} tỷ đồng"
        if amount >= 1_000_000:
            val = amount / 1_000_000
            if val == int(val):
                return f"{int(val)} triệu đồng"
            if val * 10 == int(val * 10):
                return f"khoảng {val:.1f} triệu đồng"
            return f"gần {int(val) + 1} triệu đồng"
        if amount >= 1_000:
            val = amount / 1_000
            return f"{int(val)} nghìn đồng"
        return f"{int(amount)} đồng"

    async def _heuristic_classify(
        self,
        combined_lower: str,
        user_id: str,
        ctx: Optional[dict] = None,
        intent_map: Optional[dict] = None,
        norm_query: Optional[str] = None
    ) -> Optional[IntentResponse]:
        """V56.0: Delegated to heuristic_classifier.py (Rule 1.3: <300 LOC)."""
        return await heuristic_classify(combined_lower, user_id, context=ctx, intent_map=intent_map, norm_query=norm_query)

    def _error_response(self, msg: str) -> IntentResponse:
        return IntentResponse(
            status="error",
            action=IntentAction.READ,
            message=msg,
            router_tier=RouterTier.TIER_2_SEMANTIC,
            cost_tokens=0.0
        )

orchestrator = RouterOrchestrator()
