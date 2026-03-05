import os
import uuid
import logging
import warnings
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Suppress expected library warnings (Purge Campaign)
warnings.filterwarnings("ignore", message=".*Pydantic V1 functionality isn't compatible.*")
warnings.filterwarnings("ignore", message=".*now uses mean pooling instead of CLS embedding.*")

from litestar import Litestar, Request, Response, MediaType
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components
from litestar.stores.memory import MemoryStore
from litestar.datastructures import State
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.exceptions import HTTPException, ValidationException

from src.routers.intent import IntentController
from src.routers.intent_stream import IntentStreamController
from src.controllers.health import HealthController
from src.routers.mcp.router import MCPController
from src.controllers.auth import AuthController
from src.controllers.auth_extended import AuthExtendedController
from src.controllers.notifications import NotificationController
from src.controllers.auditor import AuditorController
from src.controllers.user import UserController
from src.controllers.category import CategoryController
from src.controllers.product import ProductController
from src.controllers.article import ArticleController
from src.controllers.order import OrderController
from src.controllers.settings import SettingsController

from src.controllers.chat import ChatController
from src.routers.voice_stream import stt_websocket
from src.controllers.tts_handler import TTSController
from src.middleware import AuthMiddleware
from src.body_limit import BodyLimitMiddleware

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin, SQLAlchemyAsyncConfig

load_dotenv("../../.env")

# R1.5: SQLAlchemy Async Config (pool defaults adequate for VPS 2GB)
alchemy_config = SQLAlchemyAsyncConfig(
    connection_string=os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///:memory:",
    create_all=False,
)
alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config)

import src.mcp.tools # Register tools on import

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
allowed_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "https://smartshop.test,https://admin.smartshop.test,https://api.smartshop.test")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

cors_config = CORSConfig(allow_origins=allowed_origins)

@asynccontextmanager
async def lifespan(app: Litestar):
    from src.database import engine
    from src.database.models import VoiceProfile
    from sqlalchemy import select
    from src.utils.text import normalize_vn
    
    try:
        # Pre-load Voice Profiles into Hot Cache (R30: RAM priority)
        # Chuẩn dạng: normalize_vn() đã lowercase + bỏ dấu bên trong
        async with alchemy_config.get_engine().begin() as conn:
             pass # Engine initialized via Litestar plugin

        async with alchemy_config.create_session_maker()() as session:
            stmt = select(VoiceProfile)
            results = await session.execute(stmt)
            profiles = results.scalars().all()
            
            app.state["voice_cache"] = {
                p.user_id: {
                    "wake_words":        [normalize_vn(w) for w in (p.wake_words or [])],
                    "sleep_words":       [normalize_vn(w) for w in (p.sleep_words or [])],
                    "greeting_template": p.greeting_template,
                    "capabilities":      p.capabilities or {},
                }
                for p in profiles
            }
            logger.info(f"[Trinity Core] Hot Reload Cache: {len(app.state['voice_cache'])} profiles loaded.")
        yield
    finally:
        pass

# ==========================================
# PHASE 3: DYNAMIC RATE LIMITING (R23)
# ==========================================
memory_store = MemoryStore()

global_limit = int(os.getenv("RATE_LIMIT_GLOBAL_MINUTE", "100"))

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
        stt_websocket,
        TTSController,
    ],
    middleware=[BodyLimitMiddleware, rate_limit_config.middleware, AuthMiddleware],
    cors_config=cors_config,
    stores={"memory_store": memory_store},
    state=State({"voice_cache": {}}),
    openapi_config=OpenAPIConfig(
        title="Fast Platform API Gateway", 
        version="1.0.0",
        components=Components()
    ),
    exception_handlers={Exception: global_exception_handler},
    lifespan=[lifespan],
    plugins=[alchemy_plugin]
)

