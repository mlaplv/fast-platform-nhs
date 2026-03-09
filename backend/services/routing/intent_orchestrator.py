import logging, os, asyncio, json, time, unicodedata
from typing import List, Dict, Optional, Tuple, Union
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from .tier2_cloud import Tier2CloudRouter
from .tier3_cloud import Tier3CloudRouter
from .tier2_refiner import Tier2Refiner
from .stt_corrector import stt_corrector
from backend.services.data_injector import data_injector
from backend.services.ai_engine.core.semantic_router import SemanticRouter, INTENT_TO_ACTION
from backend.services.xohi_memory import xohi_memory
from backend.utils.text import normalize_vn
from .heuristic_classifier import heuristic_classify

logger = logging.getLogger("api-gateway")

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

    async def classify(
        self,
        transcript: str,
        user_id: str,
        app_state: object,
        context: Optional[List[Dict[str, object]]] = None,
        screen_context: Optional[Dict[str, object]] = None,
        modality: str = "text"
    ) -> IntentResponse:
        """Phase 1: Intent Resolution (T1 -> T2 Dispatch)"""
        t0 = time.monotonic()
        m_tag = "v" if modality == "voice" else "c"
        transcript = unicodedata.normalize('NFC', transcript.strip())
        logger.info(f"--- [C.O.R.E][{m_tag}] Raw Transcript: '{transcript}' ---")
        
        # Use Redis Memory entirely instead of app_state["voice_cache"]
        import difflib
        user_profile = await xohi_memory.get_voice_profile(user_id) or {}
        ctx = await xohi_memory.get_user_context(user_id) or {}
        
        # Load STT dictionary from Redis (persistent)
        redis_stt = await xohi_memory.get_stt_dictionary(user_id)
        sys_stt = await xohi_memory.get_system_stt_overrides()
        mem_stt = ctx.get("stt_dictionary", {})
        user_dict = {**sys_stt, **redis_stt, **mem_stt}
        
        # --- PHASE 0.5: NEURAL WAKE TRIGGERS (CTO V1.9) ---
        DEFAULT_GREETING = user_profile.get("greeting_template", "Dạ, em nghe đây sếp.")
        wake_words = user_profile.get("wake_words", [])
        sleep_words = user_profile.get("sleep_words", [])
        
        # Quick STT Dict bypass for Wake/Sleep (0ms)
        transcript_lower = transcript.lower()
        for wrong, right in user_dict.items():
            if wrong in transcript_lower:
                transcript_lower = transcript_lower.replace(wrong, right)
        
        normalized_transcript = normalize_vn(transcript_lower)
        
        # 0.5.1: Heuristic High-Speed Match (0ms)
        def _match_trigger(words_list, trans):
            # Phonetic equivalence check: "kút" vs "cút", "quá" vs "cá"
            trans_pho = trans.replace("k", "c").replace("q", "c")
            for w in words_list:
                w_pho = w.replace("k", "c").replace("q", "c")
                if w in trans or w_pho in trans_pho:
                    return True
                # For very short triggers (like "cut", "xohi"), be more lenient on the ratio
                threshold = 0.8 if len(w) <= 4 else 0.9
                if difflib.SequenceMatcher(None, trans_pho, w_pho).ratio() > threshold:
                    return True
            return False

        is_wake = _match_trigger(wake_words + ["xohi"], normalized_transcript)
        is_sleep = _match_trigger(sleep_words + ["cut", "ngu di", "thoat", "tam biet"], normalized_transcript)

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
            # 0.5.3: Proactive Resume Check (Rule R81)
            # If sếp just wakes XoHi, check if there's an active campaign to report
            try:
                from backend.services.xohi.creative_studio.orchestrator import content_factory
                from backend.database.alchemy_config import alchemy_config
                from backend.database.repositories import ContentCampaignRepository
                
                session_maker = alchemy_config.create_session_maker()
                async with session_maker() as session:
                    repo = ContentCampaignRepository(session=session)
                    active = await content_factory.get_active_campaign(repo)
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
        
        if is_sleep:
            return IntentResponse(status="success", action=IntentAction.READ, message="Hẹn gặp lại sếp.", router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "HARDWARE_SLEEP", "confidence": 1.0}, cost_tokens=0.0)

        # --- PHASE 1: INTERACTIVE STT LEARNING (MOLBOOK STYLE) ---
        if ctx.get("is_confirming_stt"):
            # We are waiting for a YES/NO
            yes_keywords = ["đúng", "vâng", "yes", "ừ", "ok", "ok đi", " chuẩn", "đươc", "rồi", "chính xác", "phải", "phai"]
            no_keywords = ["không", "nhầm", "sai", "no"]
            
            lower_trans = transcript.lower()
            if any(kw in lower_trans for kw in yes_keywords) and not any(kw in lower_trans for kw in no_keywords):
                # User confirmed! Save to memory
                suspected = ctx.get("pending_stt_correction", {})
                if suspected:
                    user_dict.update(suspected)
                    ctx["stt_dictionary"] = user_dict
                    
                    # Persist to Redis (permanent) — survives container restarts
                    for wrong, right in suspected.items():
                        await stt_corrector.smart_learn(user_id, wrong, right)
                    
                    logger.info(f"[STT Learning] Memorized to Redis: {suspected}")
                    
                # Restore the cleaned transcript to continue execution silently
                transcript = ctx.get("pending_cleaned_transcript", transcript)
                logger.info(f"[STT Learning] Resuming execution with corrected transcript: '{transcript}'")
                
                # Clear state so we don't get stuck in a loop
                ctx["is_confirming_stt"] = False
                ctx["pending_stt_correction"] = {}
                await xohi_memory.set_user_context(user_id, ctx)
                
            elif any(kw in lower_trans for kw in no_keywords):
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
            # --- SEMANTIC BYPASS (LOCAL-FIRST) ---
            cleaned_transcript, suspected = await stt_corrector.correct(transcript, user_dict)
            t_stt = int((time.monotonic() - t0) * 1000)
            logger.info(f"--- [C.O.R.E][{m_tag}] Corrected: '{transcript}' -> '{cleaned_transcript}' ({t_stt}ms) ---")
            
            # If the transcript was cleaned locally or by AI, and it's 100% clear (no suspect),
            # we should immediately try T1 Semantic Router and Heuristics BEFORE T2 LLM.
            if not suspected:
                # 2. Heuristic Filter (0-Token, <1ms)
                heur_res = await self._heuristic_classify(cleaned_transcript.lower(), user_id, app_state)
                if heur_res:
                    if heur_res.data is None:
                        heur_res.data = {}
                    heur_res.data["cleaned_transcript"] = cleaned_transcript
                    t_heur = int((time.monotonic() - t0) * 1000)
                    logger.info(f"[Heuristic Bypass] Classified in {t_heur}ms: {heur_res.data.get('intent_type')} target={heur_res.data.get('target')}")
                    return heur_res
            
            # Restore original flow for suspected/ambiguous ones
            if suspected:
                # Intercept! Ask for confirmation
                ctx["is_confirming_stt"] = True
                ctx["pending_stt_correction"] = suspected
                ctx["pending_cleaned_transcript"] = cleaned_transcript
                await xohi_memory.set_user_context(user_id, ctx)
                
                # Format a friendly confirmation message
                wrong_word = list(suspected.keys())[0]
                right_word = suspected[wrong_word]
                
                msg = f"Dạ, có phải ý sếp là '{right_word}' không ạ?"
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
                "CONTENT_REJECT": IntentAction.CONTENT_REJECT}
                
                # If action gives us HARDWARE_SLEEP, bypass the regular enum mapping
                # and put it directly into the data payload to trigger the frontend event, 
                # but keep the intent enum as READ to pass Pydantic validation.
                action_str = mapping.get("action", "READ")
                action = action_map.get(action_str, IntentAction.READ)
                msg_val = mapping.get("message", "")
                
                logger.info(f"[T1.5] HIT (score={sem_score:.3f}): {sem_intent} → {mapping['intent_type']}")
                return IntentResponse(
                    status="success",
                    action=action,
                    message=msg_val,
                    router_tier=RouterTier.TIER_1_HEURISTIC,
                    cost_tokens=0.0,
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

        # 3. T2 FAILED → HEURISTIC FALLBACK (0-Token, <1ms)
        #    Classify straightforward queries by keyword WITHOUT LLM
        if not result:
            result = await self._heuristic_classify(combined_lower, user_id, app_state)
            if result:
                logger.debug(f"[Heuristic Fallback] Classified: {result.data}")

        if not result:
            return self._error_response("Ý sếp chưa rõ lắm, sếp nói chi tiết hơn giúp em nhé.")


        intent_data = result.data or {}
        if result.data is None:
            result.data = {}
        result.data["cleaned_transcript"] = transcript
        
        intent_type = intent_data.get("intent_type", "UNKNOWN")
        if intent_type == "UNKNOWN":
            # Route to T3 with hardened Absolute Boundary prompt for polite rejection
            logger.debug(f"[C.O.R.E][{m_tag}] UNKNOWN intent → Routing to T3 for boundary-aware response")
            return result

        return result

    async def execute(
        self,
        classification: IntentResponse,
        transcript: str,
        context: Optional[List[Dict[str, object]]] = None,
        screen_context: Optional[Dict[str, object]] = None,
        **kwargs
    ) -> IntentResponse:
        """Phase 2: Action Execution (Phase 3 of Trinity Loop)"""
        start_time = time.monotonic()
        intent_data = classification.data or {}
        
        # VERY IMPORTANT: Use the cleaned transcript from classification payload to prevent STT hallucinations down the pipeline
        transcript = intent_data.get("cleaned_transcript", transcript)
        
        intent_type = intent_data.get("intent_type", "UNKNOWN")

        # 1. RÚT ACTION AN TOÀN CHỐNG CRASH
        class_action_str = classification.action.value if hasattr(classification.action, "value") else str(classification.action)
        modality = kwargs.get("modality", "text")
        m_tag = "v" if modality == "voice" else "c"

        if intent_type == "DEEP_ANALYSIS" or intent_type == "UNKNOWN" or class_action_str == "ANALYZE":
            logger.debug(f"[C.O.R.E][{m_tag}] Executing T3 Reasoning (intent_type={intent_type})")
            
            # RAG: Inject vector search context for grounded reasoning
            rag_context = ""
            try:
                from backend.services.ai_engine.core.vector_memory import VectorMemory
                # Detect if query involves products or articles
                lower_t = transcript.lower()
                if any(kw in lower_t for kw in ["sản phẩm", "hàng", "tồn kho", "giá", "product"]):
                    rag_context = await VectorMemory.search(transcript, session=None, context_type="product", limit=3)
                elif any(kw in lower_t for kw in ["bài viết", "tin tức", "chính sách", "article", "news"]):
                    rag_context = await VectorMemory.search(transcript, session=None, context_type="article", limit=3)
            except Exception as e:
                logger.debug(f"[RAG] Vector search skipped: {e}")
            
            # Append RAG to transcript for T3
            enriched_transcript = transcript
            if rag_context and rag_context not in ["", "Hệ thống vector hóa đang bảo trì."]:
                enriched_transcript = f"{transcript}\n\n[DỮ LIỆU THAM KHẢO TỪ HỆ THỐNG]\n{rag_context}"
                logger.info(f"[RAG] Injected {len(rag_context)} chars of context into T3")
            
            return await self.t3_router.reason(enriched_transcript, context, screen_context=screen_context)

        # ══════════════════════════════════════════
        # V62.1: CONTENT_CREATE → Content Factory Pipeline
        # ══════════════════════════════════════════
        if intent_type == "CONTENT_CREATE" or class_action_str == "CONTENT_CREATE":
            logger.info(f"[C.O.R.E][{m_tag}] Delegating to Content Factory V62.1. kwargs keys: {list(kwargs.keys())}")
            from backend.services.xohi.creative_studio.orchestrator import content_factory
            return await content_factory.handle_voice_request(
                transcript, context, 
                campaign_repo=kwargs.get("campaign_repo"),
                user_id=kwargs.get("user_id") # Rule R86: Propagate identity
            )

        if intent_type == "CONTENT_APPROVE" or class_action_str == "CONTENT_APPROVE":
            logger.info(f"[C.O.R.E][{m_tag}] Approving Content Campaign...")
            from backend.services.xohi.creative_studio.orchestrator import content_factory
            campaign_repo = kwargs.get("campaign_repo")
            latest = await content_factory.get_latest_pending(campaign_repo)
            if latest:
                return await content_factory.approve_step(latest.id, {"approved": True, "step": latest.current_step}, campaign_repo)
            return self._error_response("Dạ sếp muốn duyệt gì ạ? Hiện tại em chưa thấy có yêu cầu nào đang chờ duyệt.")

        if intent_type == "CONTENT_REJECT" or class_action_str == "CONTENT_REJECT":
            logger.info(f"[C.O.R.E][{m_tag}] Retrying/Rejecting Content Campaign...")
            from backend.services.xohi.creative_studio.orchestrator import content_factory
            campaign_repo = kwargs.get("campaign_repo")
            latest = await content_factory.get_latest_pending(campaign_repo)
            if latest:
                return await content_factory.retry_step(latest.id, campaign_repo)
            return self._error_response("Dạ sếp muốn tạo lại gì ạ? Hiện tại em chưa thấy có bài viết nào đang dở.")

        # ══════════════════════════════════════════

        # DEFAULT: UI_NAV / DATA_QUERY → Xử lý Hybrid Loop
        # ══════════════════════════════════════════
        logger.debug(f"[T2] {intent_type} → Passing to Data Injector")
        
        t2_response = await data_injector.inject(classification, transcript, **kwargs)

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
                    timeframe_vi = {
                        "today": "hôm nay",
                        "this_month": "tháng này",
                        "this_week": "tuần này",
                        "yesterday": "hôm qua",
                        "last_month": "tháng trước",
                        "none": ""
                    }.get(t2_response.data.get("timeframe"), "này")
                    
                    target_vi = {
                        "revenue": "doanh số",
                        "order": "số đơn hàng",
                        "product": "số sản phẩm",
                        "user": "số khách hàng"
                    }.get(target, target)
                    
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
            target_vi = {
                "revenue":  "biểu đồ doanh thu",
                "order":    "quản lý đơn hàng",
                "product":  "quản lý sản phẩm",
                "user":     "danh sách nhân viên",
                "category": "quản lý danh mục",
                "news":     "quản lý bài viết",
                "settings": "cài đặt giọng nói"
            }.get(target, "trang quản trị")
            t2_response.message = f"Dạ sếp, em mở {target_vi} cho sếp ngay đây ạ."

        # --- LOG MODALITY BRACKETING (XOHI[tag] for UI) ---
        # We modify the router_tier string to include the modality prefix
        if hasattr(t2_response, "router_tier"):
            raw_tier = t2_response.router_tier.value if hasattr(t2_response.router_tier, "value") else str(t2_response.router_tier)
            # Format: 'v][t1' -> passed as data to prevent schema breakdown
            if t2_response.data is None:
                t2_response.data = {}
            t2_response.data["source_tag"] = m_tag
            t2_response.data["router_tier_label"] = f"t{raw_tier}"
                
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

    async def _heuristic_classify(self, combined_lower: str, user_id: str, app_state: object) -> Optional[IntentResponse]:
        """V56.0: Delegated to heuristic_classifier.py (Rule 1.3: <300 LOC)."""
        return await heuristic_classify(combined_lower, user_id, app_state)

    def _error_response(self, msg: str) -> IntentResponse:
        return IntentResponse(
            status="error",
            action=IntentAction.READ,
            message=msg,
            router_tier=RouterTier.TIER_2_SEMANTIC,
            cost_tokens=0.0
        )

orchestrator = RouterOrchestrator()
