import os
import uuid
import logging
import warnings
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Suppress expected library warnings (Purge Campaign)
warnings.filterwarnings("ignore", message=".*Pydantic V1 functionality isn't compatible.*")
warnings.filterwarnings("ignore", message=".*now uses mean pooling instead of CLS embedding.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic_ai")

from litestar import Litestar, Request, Response, MediaType
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components
from litestar.stores.memory import MemoryStore
from litestar.datastructures import State
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.exceptions import HTTPException, ValidationException

from backend.routers.intent import IntentController
from backend.routers.intent_stream import IntentStreamController
from backend.routers.pulse_stream import PulseStreamController
from backend.controllers.health import HealthController
from backend.routers.mcp.router import MCPController
from backend.controllers.auth import AuthController
from backend.controllers.auth_extended import AuthExtendedController
from backend.controllers.notifications import NotificationController
from backend.controllers.auditor import AuditorController
from backend.controllers.user import UserController
from backend.controllers.category import CategoryController
from backend.controllers.product import ProductController
from backend.controllers.article import ArticleController
from backend.controllers.order import OrderController
from backend.controllers.settings import SettingsController

from backend.controllers.chat import ChatController
from backend.routers.content_router import ContentController
from backend.routers.voice_stream import stt_websocket
from backend.controllers.tts_handler import TTSController
from backend.middleware import AuthMiddleware
from backend.body_limit import BodyLimitMiddleware

from backend.database import alchemy_config
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

load_dotenv(".env")

# R72 CRITICAL: LiteLLM prioritizes GOOGLE_API_KEY over GEMINI_API_KEY.
# .env contains a stale GOOGLE_API_KEY (403 PERMISSION_DENIED).
# Pop it globally so ALL routers use GEMINI_API_KEY array exclusively.
os.environ.pop("GOOGLE_API_KEY", None)
os.environ.pop("GOOGLE_API_KEY_1", None)
os.environ.pop("GOOGLE_API_KEY_2", None)

# R1.5 Unified Engine Integration
alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config.litestar_config)

import backend.mcp.tools # Register tools on import

logger = logging.getLogger("api-gateway")


# ==========================================
# R24: GLOBAL EXCEPTION HANDLER (Anti Info-Disclosure)
# ==========================================
def global_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Catches ALL unhandled exceptions and returns a sanitized JSON response.
    NEVER leaks stack traces, DB schemas, or internal paths to the client.
    Logs full details server-side with a trace ID for debugging.
    """
    trace_id = str(uuid.uuid4())[:8]

    # Handle standard HTTP Client Errors (4xx) gracefully
    if isinstance(exc, HTTPException) and exc.status_code < 500:
        if exc.status_code == 401:
            logger.debug(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        else:
            logger.warning(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        return Response(
            media_type=MediaType.JSON,
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "trace_id": trace_id,
            },
        )
    
    # Handle Litestar Pydantic Validation Errors
    if isinstance(exc, ValidationException):
        logger.warning(f"[TRACE:{trace_id}] Validation Error: {exc.detail}")
        return Response(
            media_type=MediaType.JSON,
            status_code=400,
            content={
                "detail": "Data validation failed",
                "errors": exc.extra if hasattr(exc, "extra") else str(exc),
                "trace_id": trace_id,
            },
        )

    # Genuine 500 Internal Server Errors (Masked)
    logger.error(f"[TRACE:{trace_id}] Unhandled {type(exc).__name__}: {exc}", exc_info=True)
    return Response(
        media_type=MediaType.JSON,
        status_code=500,
        content={
            "detail": "An internal error occurred. Please contact support.",
            "trace_id": trace_id,
        },
    )

# CORS configs from env (R4 - Zero-Trust CORS)
# Rule 1.4: Single Source of Truth (.env) - BẮT BUỘC khai báo mọi URL từ .env
admin_url = os.getenv("ADMIN_URL", "https://admin.smartshop.test")
api_url = os.getenv("API_URL", "https://api.smartshop.test")
store_url = os.getenv("APP_URL", "https://smartshop.test")

allowed_origins = [admin_url, api_url, store_url]
# Fallback to backend config if provided
allowed_origins_str = os.getenv("BACKEND_CORS_ORIGINS")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

cors_config = CORSConfig(allow_origins=allowed_origins, allow_credentials=True)

# Allowed Hosts (R4.1 Zero-Trust Infrastructure)
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "smartshop.test,api.smartshop.test,admin.smartshop.test")
allowed_hosts = [h.strip() for h in allowed_hosts_str.split(",")]
from litestar.config.allowed_hosts import AllowedHostsConfig
allowed_hosts_config = AllowedHostsConfig(allowed_hosts=allowed_hosts)

@asynccontextmanager
async def lifespan(app: Litestar):
    from backend.database.models import VoiceProfile
    from sqlalchemy import select
    from backend.utils.text import normalize_vn
    from backend.services.event_bus import event_bus
    from backend.services.xohi_responder import setup_subscriptions
    from backend.services.xohi.creative_studio.orchestrator import content_factory
    from backend.utils.http_client import SharedHttpClient
    
    # Start Proactive Nerve System (V56.5)
    setup_subscriptions()
    await event_bus.start()
    
    import asyncio as _aio
    heartbeat_task = None  # Guard: prevent UnboundLocalError if lifespan crashes early
    purge_task = None
    try:
        # Pre-load Voice Profiles into Hot Cache (R30: RAM priority)
        # Chuẩn dạng: normalize_vn() đã lowercase + bỏ dấu bên trong
        async with alchemy_config.get_engine().begin() as conn:
             pass # Engine initialized via Litestar plugin

        async with alchemy_config.create_session_maker()() as session:
            stmt = select(VoiceProfile)
            results = await session.execute(stmt)
            profiles = results.scalars().all()
            
            from backend.services.xohi_memory import xohi_memory
            
            count = 0
            for p in profiles:
                profile_data = {
                    "wake_words":        [normalize_vn(w) for w in (p.wake_words or [])],
                    "sleep_words":       [normalize_vn(w) for w in (p.sleep_words or [])],
                    "greeting_template": p.greeting_template,
                    "capabilities":      p.capabilities or {},
                }
                await xohi_memory.cache_voice_profile(str(p.user_id), profile_data)
                count += 1
                
            logger.info(f"[Trinity Core] Hot Reload Cache: {count} profiles loaded to Redis.")

        # V56.0 Phase 2: Zero-Cold-Start — Pre-load Embedding Model
        try:
            from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
            await _aio.wait_for(warmup_encoder(), timeout=30)
            logger.info("[Trinity Core] Embedding model pre-loaded (Zero-Cold-Start).")
        except Exception as e:
            logger.critical(f"[Trinity Core] Embedding warmup FAILED: {e}")

        # V56.0 Phase 2: Pre-compute SemanticRouter intent centroids
        try:
            from backend.services.ai_engine.core.semantic_router import SemanticRouter
            _sr = SemanticRouter()
            await _aio.wait_for(_sr.warmup(), timeout=30)
            logger.info("[Trinity Core] SemanticRouter centroids pre-computed.")
        except Exception as e:
            logger.critical(f"[Trinity Core] SemanticRouter warmup FAILED: {e}")

        # V56.0 Phase 3: Autonomous Heartbeat — internal background loop
        # No cron, no curl, no APScheduler. Pure asyncio.
        scan_interval = int(os.getenv("ANOMALY_SCAN_INTERVAL", "900"))  # 15 min default

        async def _heartbeat_loop():
            from backend.services.anomaly_detector import AnomalyDetector
            detector = AnomalyDetector()
            session_maker = alchemy_config.create_session_maker()
            await _aio.sleep(60)  # Wait 1 min after boot before first scan
            while True:
                try:
                    async with session_maker() as session:
                        alerts = await detector.scan(session)
                        if alerts:
                            logger.info(f"[Heartbeat] {len(alerts)} anomalies detected.")
                except Exception as e:
                    logger.warning(f"[Heartbeat] Scan failed (non-fatal): {e}")
                await _aio.sleep(scan_interval)

        heartbeat_task = _aio.create_task(_heartbeat_loop())
        logger.info(f"[Trinity Core] Heartbeat started (interval={scan_interval}s).")

        # ═══ AUTO-PURGE: Chat Log Cleanup (Rule 1.11 compliant) ═══
        purge_interval = int(os.getenv("CHAT_PURGE_INTERVAL", "21600"))  # 6h default

        async def _auto_purge_loop():
            from datetime import datetime, timedelta, timezone
            from sqlalchemy import delete as sql_delete
            from backend.database.models import ChatMessage, VoiceProfile as VP
            session_maker = alchemy_config.create_session_maker()
            await _aio.sleep(300)  # Wait 5 min after boot
            while True:
                try:
                    async with session_maker() as session:
                        profiles = (await session.execute(select(VP.user_id, VP.chat_settings))).all()
                        total_purged = 0
                        for row in profiles:
                            days = (row.chat_settings or {}).get("auto_purge_days", 30)
                            if not days or days <= 0:
                                continue
                            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                            stmt = sql_delete(ChatMessage).where(
                                ChatMessage.user_id == row.user_id,
                                ChatMessage.created_at < cutoff
                            )
                            result = await session.execute(stmt)
                            total_purged += result.rowcount
                        await session.commit()
                        if total_purged > 0:
                            logger.info(f"[AutoPurge] Cleaned {total_purged} expired chat messages.")
                except Exception as e:
                    logger.warning(f"[AutoPurge] Cycle failed (non-fatal): {e}")
                await _aio.sleep(purge_interval)

        purge_task = _aio.create_task(_auto_purge_loop())
        logger.info(f"[Trinity Core] AutoPurge started (interval={purge_interval}s).")
        
        # V61.0: Self-Healing Resume for Content Factory
        _aio.create_task(content_factory.resume_all())

        yield
    finally:
        # Graceful shutdown — guard against early crash (BUG-1 fix)
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except _aio.CancelledError:
                pass
            logger.info("[Trinity Core] Heartbeat stopped.")
        
        if purge_task is not None:
            purge_task.cancel()
            try:
                await purge_task
            except _aio.CancelledError:
                pass
            logger.info("[Trinity Core] AutoPurge stopped.")
        
        # Stop Proactive Nerve System
        await event_bus.stop()
        
        # R106: Recycle Shared HTTP Client
        await SharedHttpClient.close()
        
        logger.info("[Trinity Core] EventBus & HTTP Client stopped.")

# ==========================================
# PHASE 3: DYNAMIC RATE LIMITING (R23)
# ==========================================
memory_store = MemoryStore()

global_limit = int(os.getenv("RATE_LIMIT_GLOBAL_MINUTE", "200"))

rate_limit_config = RateLimitConfig(
    rate_limit=("minute", global_limit),
    exclude=["/health", "/metrics", "/schema"],
    store="memory_store"
)

# Unified Route Registration (Phase 6 Real Notifications)
app = Litestar(
    route_handlers=[
        IntentController, 
        IntentStreamController,
        PulseStreamController,
        HealthController, 
        MCPController, 
        AuthController, 
        AuthExtendedController, 
        NotificationController,
        AuditorController,
        UserController,
        CategoryController,
        ProductController,
        ArticleController,
        OrderController,
        ChatController,
        SettingsController,
        ContentController,
        stt_websocket,
        TTSController,
    ],
    middleware=[BodyLimitMiddleware, rate_limit_config.middleware, AuthMiddleware],
    cors_config=cors_config,
    # allowed_hosts=allowed_hosts_config,
    stores={"memory_store": memory_store},
    openapi_config=OpenAPIConfig(
        title="Fast Platform API Gateway", 
        version="1.0.0",
        components=Components()
    ),
    exception_handlers={Exception: global_exception_handler},
    lifespan=[lifespan],
    plugins=[alchemy_plugin]
)
