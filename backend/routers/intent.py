from litestar import Controller, post, Request
from litestar.di import Provide
from litestar.repository.filters import LimitOffset
from backend.schemas.intent import IntentRequest, IntentResponse, IntentAction, RouterTier
from backend.services.intent_orchestrator import orchestrator
from backend.services.ai_engine.semantic_shield import SemanticShield
import json, time, hashlib, uuid, asyncio, logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.user_service import user_service
from backend.services.chat_service import chat_service
from backend.services.telemetry_service import telemetry_service

logger = logging.getLogger("api-gateway")

# Tên tiếng Việt của từng IntentAction — dùng trong Skill Guard thông báo lỗi
from backend.constants.action_vi import ACTION_VI

# ui_action → target entity (dùng trong heuristic fallback)
UI_ACTION_TARGET = {
    "show_order_management":   "order",
    "show_product_management": "product",
    "show_user_management":    "user",
    "show_user_table":         "user",
    "show_revenue_chart":      "revenue",
}

# Keywords kích hoạt heuristic COUNT (check trên combined_lower = gốc + sau-STT)
COUNT_KEYWORDS = ["bao nhiêu", "mấy", "tổng số", "dân số", "doanh thu", "doanh số"]


class IntentController(Controller):
    """
    Phễu Lọc 3 Tầng — API Gateway Entry Point
    Tier 1 (Heuristic) → Tier 2 (Semantic SLM) → Tier 3 (Cloud LLM)
    """
    path = "/api/v1/intent"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shield = SemanticShield()

    @post("/")
    async def process_intent(
        self,
        request: Request,
        data: IntentRequest,
        db_session: AsyncSession,
    ) -> IntentResponse:
        """
        Phễu Lọc 3 Tầng — [THIẾT QUÂN LUẬT] Fully Service-based.
        """
        start_time = time.monotonic()
        session_id = data.session_id or str(uuid.uuid4())

        try:
            # ── Jailbreak scan (STT corrections removed — Groq Whisper handles accuracy) ──
            if not self.shield.scan(data.query):
                return _error("Lõi nhận thức gián đoạn...")

            # ── Resolve user_id từ JWT ──
            user_info = getattr(request.state, "user", None)
            user_id = None
            if user_info:
                # Rule R86: Prefer direct ID from JWT for performance and consistency
                user_id = user_info.get("id")
                if not user_id and "sub" in user_info:
                    user_data = await user_service.get_user_by_email(db_session, user_info["sub"])
                    if user_data:
                        user_id = user_data["id"]

            # ── Lịch sử hội thoại (10 tin) ──
            context = await chat_service.get_recent_messages(db_session, session_id, limit=10)

            # ── TRINITY PHASE 1: Classification (Dispatcher) ──
            # Orchestrator handles T1 (Heuristic) and T2 (LLM Dispatcher)
            result = await orchestrator.classify(
                transcript=data.query,
                user_id=user_id,
                app_state=request.app.state,
                context=context,
                screen_context=data.screen_context,
                modality=data.modality
            )

            # ── TRINITY PHASE 2: Skill Guard (Constitutional Protection) ──
            # Guard runs BEFORE expensive Data Injection/Reasoning
            if user_id and result.status != "error":
                # [XOHI] Zero-Hydration: Check profile via xohi_memory (Redis-first) or direct DB
                from backend.services.xohi_memory import xohi_memory
                profile = await xohi_memory.get_voice_profile(user_id)
                if profile and profile.get("capabilities"):
                    caps = profile["capabilities"] if isinstance(profile["capabilities"], dict) else json.loads(profile["capabilities"])
                    action = result.action.value if hasattr(result.action, "value") else result.action
                    check = "READ" if action == "COUNT" else action
                    if not caps.get(check, True):
                        result.status  = "error"
                        result.message = f"Dạ, năng lực '{ACTION_VI.get(action, action)}' đang tạm khóa. Sếp bật lại trong Cài đặt Giọng nói để em hỗ trợ ạ."
                        result.data    = {"restricted": True, "action": action}

            # ── TRINITY PHASE 3: Execution (Provider -> Refiner) ──
            # Only execute Trinity Loop or Tier 3 if NOT restricted
            # BẮT BUỘC: Bỏ qua Execute cho SESSION_CTRL (Wake/Sleep) — đã hoàn thành ở T1
            # Tuy nhiên, UI_NAV cần Execute để Inject dữ liệu (ví dụ: Biểu đồ)
            intent_data = result.data or {}
            intent_type = intent_data.get("intent_type")
            result_category = intent_data.get("category")

            if result.status != "error" and (result_category != "SESSION_CTRL" or intent_type == "UI_NAV"):
                try:
                    # GLOBAL TIMEOUT GUARD: Force response within 20s to prevent hanging
                    result = await asyncio.wait_for(
                        orchestrator.execute(
                            classification=result,
                            transcript=data.query,
                            context=context,
                            screen_context=data.screen_context,
                            db_session=db_session,
                            modality=data.modality,
                            user_id=user_id # Propagate identity for R86
                        ),
                        timeout=45.0 # Increased to 45s to tolerate TrinityBridge 429 backoff & key rotation
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[Gateway Timeout] Request hung too long: {data.query}")
                    return _error("Giao thức kết nối đang bận, Sếp đợi em một chút hoặc thử lại sau nhé.")

            tier_str = str(result.router_tier.value if hasattr(result.router_tier, "value") else result.router_tier)

            # ── Telemetry (background) ──
            asyncio.create_task(telemetry_service.log_telemetry(
                db_session,
                session_id,
                f"TrinityCore-Tier_{tier_str}",
                hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                getattr(result, "input_tokens", 0),
                getattr(result, "output_tokens", 0),
                float(result.cost_tokens),
                int((time.monotonic() - start_time) * 1000)
            ))

            # ── Message Persistence (Background) ──
            ui_action = (result.data or {}).get("ui_action")
            action_val = result.action.value if hasattr(result.action, "value") else result.action

            asyncio.create_task(chat_service.save_message(db_session, session_id, "user", data.query, user_id=user_id, modality=data.modality))

            # Rule R86: Selective Persistence — Skip assistant save if Responder handles it (e.g. Content Factory)
            if action_val != "CONTENT_CREATE":
                payload_extra = {"ui_action": ui_action, "router_tier": tier_str, **(result.data or {})}
                asyncio.create_task(chat_service.save_message(db_session, session_id, "assistant", result.message, user_id=user_id, modality=data.modality, data_extra=payload_extra))

            return result

        except Exception as e:
            logger.exception(f"[Gateway Error] {e}")
            return _error("Giao thức kết nối đang bận, Sếp đợi em một chút hoặc thử lại sau nhé.")


def _error(msg: str) -> IntentResponse:
    """Shortcut trả lỗi chuẩn — tránh lặp 3 field mỗi lần."""
    return IntentResponse(status="error", action=IntentAction.READ, message=msg,
                          router_tier=None, cost_tokens=0.0)
