import logging
import time
from typing import Optional, List, Dict
from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from .tier1_semantic import Tier1SemanticRouter
from .tier2_cloud import Tier2CloudRouter
from .tier3_cloud import Tier3CloudRouter
from .tier2_refiner import Tier2Refiner
from src.services.data_injector import data_injector

logger = logging.getLogger("api-gateway")

class RouterOrchestrator:
    """
    C.O.R.E ARCHITECTURE — Central Orchestrated Routing Engine
    ============================================================
    T1 (Local, 0ms) → T2 (Dispatcher) → Trinity Loop (Inject + Refine).
    """
    def __init__(self):
        self.t1_router = Tier1SemanticRouter()
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
    ) -> IntentResponse:
        """Phase 1: Intent Resolution (T1 -> T2 Dispatch)"""
        logger.info(f"--- [C.O.R.E] Classifying: '{transcript}' ---")
        
        # 1. TIER 1: Local Semantic Match (0-Token, <10ms)
        t1_response = self.t1_router.route(transcript, user_id, app_state)
        if t1_response is not None:
            logger.info(f"[T1] HIT: {t1_response.data.get('ui_action')}")
            return t1_response

        combined_lower = transcript.lower()

        # 2. TIER 2: Central Dispatcher (Flash)
        result = None
        try:
            result = await self.t2_router.extract(transcript, context=context, screen_context=screen_context)
        except Exception as e:
            logger.error(f"[T2] Dispatch Failure: {e}")

        # 3. T2 FAILED → HEURISTIC FALLBACK (0-Token, <1ms)
        #    Classify straightforward queries by keyword WITHOUT LLM
        if not result:
            result = self._heuristic_classify(combined_lower, user_id, app_state)
            if result:
                logger.info(f"[Heuristic Fallback] Classified: {result.data}")

        if not result:
            return self._error_response("Ý sếp chưa rõ lắm, sếp nói chi tiết hơn giúp em nhé.")

        # 4. HEURISTIC SAFETY NET (post-T2 correction)
        COUNT_KEYWORDS = ["bao nhiêu", "mấy", "tổng số", "doanh thu", "doanh số"]
        CHART_KEYWORDS = ["bieu do", "biểu đồ", "mo ", "xem "]
        
        if any(kw in combined_lower for kw in COUNT_KEYWORDS) and not any(kw in combined_lower for kw in CHART_KEYWORDS):
            result.action = IntentAction.COUNT
            data = result.data or {}
            data.update({"intent_type": "DATA_QUERY", "action": "COUNT"})
            if data.get("target") not in ["order", "product", "user", "revenue"]:
                data["target"] = ("revenue" if ("doanh thu" in combined_lower or "doanh số" in combined_lower)
                                 else "product")
            result.data = data

        intent_data = result.data or {}
        intent_type = intent_data.get("intent_type", "UNKNOWN")
        if intent_type == "UNKNOWN":
            # Route to T3 with hardened Absolute Boundary prompt for polite rejection
            logger.info("[C.O.R.E] UNKNOWN intent → Routing to T3 for boundary-aware response")
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
        intent_type = intent_data.get("intent_type", "UNKNOWN")

        # 1. RÚT ACTION AN TOÀN CHỐNG CRASH
        class_action_str = classification.action.value if hasattr(classification.action, "value") else str(classification.action)

        if intent_type == "DEEP_ANALYSIS" or intent_type == "UNKNOWN" or class_action_str == "ANALYZE":
            logger.info(f"[C.O.R.E] Executing T3 Reasoning (intent_type={intent_type})")
            return await self.t3_router.reason(transcript, context, screen_context=screen_context)

        # ══════════════════════════════════════════
        # DEFAULT: UI_NAV / DATA_QUERY → Xử lý Hybrid Loop
        # ══════════════════════════════════════════
        logger.info(f"[T2] {intent_type} → Passing to Data Injector")
        
        t2_response = await data_injector.inject(classification, transcript, **kwargs)

        # 2. KIỂM TRA ACTION AN TOÀN CỦA T2
        t2_action_str = t2_response.action.value if hasattr(t2_response.action, "value") else str(t2_response.action)

        # --- TRINITY LOOP (NLG REFINER) ---
        # Nếu là lệnh đếm số liệu, dùng Refiner để làm mượt câu chữ
        if intent_type == "DATA_QUERY" or t2_action_str == "COUNT":
            raw_data = t2_response.data.get("injected_count") or t2_response.data.get("raw_count")
            if raw_data is not None:
                logger.info("[Trinity Loop] Enhancing raw data with NLG Refiner...")
                target = t2_response.data.get("target", "")
                
                # 3. NHẬN CẢ MESSAGE VÀ COST, CỘNG DỒN VÀO BILL (Hàm refine giờ LUÔN trả về msg)
                refined_msg, refine_cost = await self.t2_refiner.refine(transcript, target, str(raw_data))
                
                t2_response.message = refined_msg
                # CỘNG DỒN CHI PHÍ TOKEN CỦA REFINER
                t2_response.cost_tokens = (t2_response.cost_tokens or 0) + refine_cost
                logger.info(f"[Trinity Loop] Refined Msg: {refined_msg} (Cost: {refine_cost} tokens)")

        duration = int((time.monotonic() - start_time) * 1000)
        logger.info(f"[C.O.R.E] Trinity Loop Complete in {duration}ms")
        return t2_response

    def _heuristic_classify(self, combined_lower: str, user_id: str, app_state: object) -> Optional[IntentResponse]:
        """
        Zero-LLM Heuristic Fallback — classify known patterns by keyword.
        Only handles clear-cut queries. Returns None for ambiguous ones.
        """
        # --- Detect TARGET ---
        target = "none"
        if any(kw in combined_lower for kw in ["doanh thu", "doanh số", "doanh so", "biểu đồ", "bieu do", "tiền"]):
            target = "revenue"
        elif any(kw in combined_lower for kw in ["đơn hàng", "don hang", "hoa don", "bill"]):
            target = "order"
        elif any(kw in combined_lower for kw in ["sản phẩm", "san pham", "tồn kho", "tong kho", "kho hang"]):
            target = "product"
        elif any(kw in combined_lower for kw in ["người dùng", "khách", "nhân viên", "nhan vien", "tai khoan"]):
            target = "user"
        elif any(kw in combined_lower for kw in ["danh mục", "danh muc"]):
            target = "category"
        elif any(kw in combined_lower for kw in ["tin tức", "tin tuc", "bài viết", "bai viet"]):
            target = "news"

        if target == "none":
            return None

        # --- Detect TIMEFRAME ---
        timeframe = "none"
        if "hôm nay" in combined_lower or "hom nay" in combined_lower:
            timeframe = "today"
        elif "tháng này" in combined_lower or "thang nay" in combined_lower:
            timeframe = "this_month"
        elif "tuần này" in combined_lower or "tuan nay" in combined_lower:
            timeframe = "this_week"

        # ═══ TIMEFRAME INHERITANCE (V58.3) ═══
        voice_cache = getattr(app_state, "voice_cache", {})
        user_profile = voice_cache.get(user_id, {})
        
        if timeframe == "none" and target == "revenue":
            # If follow-up message about revenue/chart, reuse last timeframe
            timeframe = user_profile.get("last_revenue_timeframe", "none")
            logger.info(f"[Heuristic] Inherited timeframe: {timeframe}")
        
        # Update context for next query
        if target == "revenue":
            user_profile["last_revenue_timeframe"] = timeframe
            voice_cache[user_id] = user_profile

        # --- Detect INTENT TYPE ---
        count_keywords = ["bao nhiêu", "mấy", "tổng số", "tổng", "bao nhieu"]
        # Vietnamese question patterns: "có ... nào", "có ... mới", "có ... không"
        question_keywords = ["nào", "nao", "mới", "moi", "có không", "co khong", "chưa", "chua", "rồi", "roi"]
        mutate_keywords = ["thêm", "tạo", "xóa", "sửa", "update", "create", "delete", "them", "tao", "xoa", "sua"]
        
        is_count = any(kw in combined_lower for kw in count_keywords)
        is_question = any(kw in combined_lower for kw in question_keywords)
        is_mutate = any(kw in combined_lower for kw in mutate_keywords)
        
        # --- Entity Extraction (Heuristic V60.0) ---
        extracted_entities: dict = {}
        verb = "create"  # default
        
        if is_mutate:
            # Detect verb
            create_kw = ["thêm", "tạo", "them", "tao", "create", "mới", "moi"]
            delete_kw = ["xóa", "xoa", "delete", "bỏ", "bo", "hủy", "huy"]
            edit_kw = ["sửa", "sua", "edit", "update", "cập nhật", "cap nhat", "đổi", "doi"]
            
            if any(kw in combined_lower for kw in delete_kw):
                verb = "delete"
            elif any(kw in combined_lower for kw in edit_kw):
                verb = "edit"
            else:
                verb = "create"
            
            # Extract name
            for marker in ["tên là ", "ten la ", "tên ", "ten "]:
                if marker in combined_lower:
                    name_part = combined_lower.split(marker)[1].strip()
                    # Clean up: take until next keyword or end
                    for stop in ["email", "mật khẩu", "vai trò", "giá", "mô tả"]:
                        if stop in name_part:
                            name_part = name_part.split(stop)[0].strip()
                    extracted_entities["name"] = name_part.title()
                    break
            
            # Extract email
            import re
            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', combined_lower)
            if email_match:
                extracted_entities["email"] = email_match.group(0)
        
        if is_mutate:
            intent_type = "MUTATE"
            action = IntentAction.MUTATE
        elif is_count or is_question:
            intent_type = "DATA_QUERY"
            action = IntentAction.COUNT
        else:
            intent_type = "UI_NAV"
            action = IntentAction.READ

        # --- Widget mapping ---
        target_to_widget = {
            "revenue": "show_revenue_chart",
            "order": "show_order_management",
            "product": "show_product_management",
            "user": "show_user_management",
            "category": "show_category_management",
            "news": "show_news_management",
        }
        widget_id = target_to_widget.get(target, "")

        # --- Mutation message ---
        mutation_msg = ""
        if intent_type == "MUTATE":
            VI_VERB = {"create": "tạo", "edit": "sửa", "delete": "xóa"}
            VI_TARGET = {"user": "nhân viên", "product": "sản phẩm", "category": "danh mục", "order": "đơn hàng", "news": "bài viết"}
            v_label = VI_VERB.get(verb, verb)
            t_label = VI_TARGET.get(target, target)
            name = extracted_entities.get("name", "")
            mutation_msg = f"Sếp muốn {v_label} {t_label}" + (f' "{name}"' if name else "") + ". Xác nhận thông tin bên dưới ạ."

        logger.info(f"[Heuristic] Result: {intent_type} target={target} verb={verb} widget={widget_id} timeframe={timeframe}")
        return IntentResponse(
            status="success",
            action=action,
            message=mutation_msg if mutation_msg else "",
            router_tier=RouterTier.TIER_1_HEURISTIC,
            cost_tokens=0.0,
            requires_confirmation=True if intent_type == "MUTATE" else False,
            data={
                "intent_type": intent_type,
                "target": target,
                "verb": verb,
                "timeframe": timeframe,
                "ui_action": widget_id,
                "widget_id": widget_id,
                "status": "none",
                "action": intent_type,
                "requires_confirmation": True if intent_type == "MUTATE" else False,
                "entities": extracted_entities
            }
        )

    def _error_response(self, msg: str) -> IntentResponse:
        return IntentResponse(
            status="error",
            action=IntentAction.READ,
            message=msg,
            router_tier=RouterTier.TIER_2_SEMANTIC,
            cost_tokens=0.0
        )

orchestrator = RouterOrchestrator()
