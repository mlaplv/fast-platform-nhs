"""Fast Platform API Gateway entry point.

This module configures environment loading, logging, warning handling, CORS, rate‑limiting,
static file routers, route grouping, and middleware ordering for the Litestar application.
"""
import os
import logging
import warnings
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# R00: Load environment before any local imports to ensure SSOT configuration
# Resolve .env relative to repository root (parents[1])
dotenv_path = Path(__file__).resolve().parents[1] / ".env"
if dotenv_path.is_file():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

from backend.app_logging import setup_logging
# Pass module name for namespaced logging if supported
setup_logging()

# Suppress library warnings (consolidated)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="pydantic|pydantic_ai",
)
# R61: Silence Pydantic V1/Alchemy legacy warnings on Python 3.14+ (System is fully V2)
warnings.filterwarnings(
    "ignore",
    message=".*Core Pydantic V1 functionality.*",
)

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components
from litestar.stores.memory import MemoryStore
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.static_files import create_static_files_router

# Handlers and Plugins
from backend.exceptions import global_exception_handler
from backend.lifespan import lifespan
from backend.database import alchemy_config
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

# Route Handlers
from backend.routers.intent import IntentController
from backend.routers.intent_stream import IntentStreamController
from backend.routers.pulse_stream import PulseStreamController
from backend.controllers.health import HealthController
from backend.routers.mcp.router import MCPController
from backend.controllers.auth import AuthController
from backend.controllers.notifications import NotificationController
from backend.controllers.auditor import AuditorController
from backend.controllers.user import UserController
from backend.controllers.category import CategoryController
from backend.controllers.product import ProductController
from backend.controllers.client.diagnostics import DiagnosticController
from backend.controllers.article import ArticleController
from backend.controllers.order import OrderController
from backend.controllers.client.checkout import CheckoutController
from backend.controllers.client.order import PublicOrderController
from backend.controllers.client.product import PublicProductController
from backend.controllers.client.category import PublicCategoryController
from backend.controllers.client.home import ClientHomeController
from backend.controllers.client.review import PublicReviewController
from backend.controllers.client.support import SupportController
from backend.controllers.client.pulse import ClientPulseController
from backend.controllers.client.news import PublicNewsController
from backend.controllers.client.user import ClientUserController
from backend.controllers.client.settings import ClientSettingsController
from backend.controllers.client.notifications import ClientNotificationController
from backend.controllers.client.seo import PublicSeoController, PublicGoogleMerchantController, PublicCrawlerSeoController
from backend.controllers.admin_support import AdminSupportController
from backend.controllers.admin_support_inbox import AdminSupportInboxController
from backend.controllers.review import AdminReviewController
from backend.controllers.promotion import PromotionController
from backend.controllers.settings import SettingsController
from backend.controllers.ai_management import AIManagementController
from backend.controllers.chat import ChatController
from backend.controllers.content import ContentController
from backend.controllers.media import MediaController
from backend.controllers.banner import BannerController
from backend.routers.content_stream import ContentStreamController
from backend.routers.voice_core import stt_websocket
from backend.controllers.tts_handler import TTSController
from backend.controllers.client.tts import PublicTTSController
from backend.routers.intent_map import IntentMapController
from backend.controllers.scheduler import SchedulerController
from backend.controllers.client.fomo import FomoController
from backend.controllers.client.viral import ViralController
from backend.controllers.client.barcode import BarcodeController
from backend.controllers.compliance import ComplianceController
from backend.controllers.ads_protection import AdsProtectionController
from backend.controllers.security import SecurityController
from backend.controllers.client.ctv import ClientCtvController
from backend.controllers.admin_ctv import AdminCtvController

from backend.middleware import AuthMiddleware
from backend.body_limit import BodyLimitMiddleware
from backend.domain_guard import DomainGuardMiddleware
from backend.audit_middleware import AuditMiddleware
from backend.stall_middleware import StallDetectorMiddleware
from backend.core.transaction_middleware import TransactionMiddleware


# R72: Unified Model Environment Sync
for key in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_1", "GOOGLE_API_KEY_2"]:
    os.environ.pop(key, None)

alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config.litestar_config)
import backend.mcp.tools 

logger = logging.getLogger("api-gateway")

# CORS configs (Rule R4: Zero-Trust)
def _build_allowed_origins() -> list[str]:
    """Construct the list of CORS origins.
    - Defaults come from ADMIN_URL, API_URL, APP_URL env vars.
    - If BACKEND_CORS_ORIGINS is set, it overrides defaults and is split by commas.
    - Basic validation ensures each origin starts with http:// or https://.
    """
    defaults = [
        os.getenv("ADMIN_URL", "https://admin.osmo.vn"),
        os.getenv("API_URL", "https://api.osmo.vn"),
        os.getenv("APP_URL", "https://osmo.vn"),
    ]
    cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS")
    if cors_origins_str:
        origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
    else:
        origins = defaults
    # Simple validation – keep only http/https schemes
    validated = [o for o in origins if o.startswith("http://") or o.startswith("https://")]
    if not validated:
        logging.warning("CORS origin list is empty after validation; falling back to defaults")
        validated = defaults
    return validated

allowed_origins = _build_allowed_origins()

cors_config = CORSConfig(allow_origins=allowed_origins, allow_credentials=True)

# Application Instance
memory_store = MemoryStore()
rate_limit_config = RateLimitConfig(
    rate_limit=("minute", int(os.getenv("RATE_LIMIT_GLOBAL_MINUTE", "1000"))),
    exclude=["/health", "/metrics", "/schema"],
    store="memory_store",
)

# Helper to create static file routers
def _static_routers() -> list:
    return [
        create_static_files_router(path="/wasm", directories=["backend/static/wasm"], name="wasm"),
        create_static_files_router(path="/vad", directories=["backend/static/vad"], name="vad"),
        create_static_files_router(path="/models", directories=["backend/static/models"], name="models"),
    ]

# Group route handlers for readability
admin_routes = [
    AdminReviewController,
    AdminSupportController,
    AdminSupportInboxController,
    AdsProtectionController,
    ComplianceController,
    SecurityController,
    PublicSeoController,
    PublicGoogleMerchantController,
    AdminCtvController,
]

client_routes = [
    PublicProductController,
    PublicCategoryController,
    ClientHomeController,
    PublicReviewController,
    SupportController,
    ClientPulseController,
    PublicNewsController,
    ClientSettingsController,
    ClientUserController,
    ClientNotificationController,
    FomoController,
    PublicTTSController,
    ViralController,
    BarcodeController,
    ClientCtvController,
    PublicCrawlerSeoController,
]

public_routes = [
    IntentController,
    IntentStreamController,
    PulseStreamController,
    HealthController,
    MCPController,
    AuthController,
    NotificationController,
    AuditorController,
    UserController,
    CategoryController,
    ProductController,
    ArticleController,
    OrderController,
    CheckoutController,
    PublicOrderController,
    ChatController,
    SettingsController,
    AIManagementController,
    ContentController,
    MediaController,
    ContentStreamController,
    BannerController,
    stt_websocket,
    TTSController,
    IntentMapController,
    SchedulerController,
    DiagnosticController,
    PromotionController,
]

# Ordered middleware – authentication early
ordered_middleware = [
    AuthMiddleware,
    DomainGuardMiddleware,
    AuditMiddleware,
    BodyLimitMiddleware,
    StallDetectorMiddleware,
    rate_limit_config.middleware,
]

app = Litestar(
    route_handlers=_static_routers() + public_routes + admin_routes + client_routes,
    middleware=ordered_middleware,
    cors_config=cors_config,
    stores={"memory_store": memory_store},
    openapi_config=OpenAPIConfig(
        title="Fast Platform API Gateway",
        version="1.0.0",
        components=Components(),
    ),
    exception_handlers={Exception: global_exception_handler},
    lifespan=[lifespan],
    plugins=[alchemy_plugin],
)
