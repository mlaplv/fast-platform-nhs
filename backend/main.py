import os
import logging
import warnings
from dotenv import load_dotenv

from backend.app_logging import setup_logging
setup_logging()

# Suppress library warnings
warnings.filterwarnings("ignore", message=".*now uses mean pooling instead of CLS embedding.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic_ai")
# R61: Silence Pydantic V1 legacy warnings on Python 3.14+ (System is fully V2)
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality isn't compatible with Python 3.14.*")

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components
from litestar.stores.memory import MemoryStore
from litestar.middleware.rate_limit import RateLimitConfig

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
from backend.controllers.article import ArticleController
from backend.controllers.order import OrderController
from backend.controllers.client.checkout import CheckoutController
from backend.controllers.client.product import PublicProductController
from backend.controllers.settings import SettingsController
from backend.controllers.ai_management import AIController
from backend.controllers.chat import ChatController
from backend.routers.content_router import ContentController
from backend.routers.media_router import MediaController
from backend.controllers.banner import BannerController
from backend.routers.content_stream import ContentStreamController
from backend.routers.voice_stream import stt_websocket
from backend.controllers.tts_handler import TTSController
from backend.routers.intent_map import IntentMapController
from backend.routers.scheduler_router import SchedulerController

from backend.middleware import AuthMiddleware
from backend.body_limit import BodyLimitMiddleware
from backend.domain_guard import DomainGuardMiddleware

load_dotenv(".env")

# R72: Unified Model Environment Sync
for key in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_1", "GOOGLE_API_KEY_2"]:
    os.environ.pop(key, None)

alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config.litestar_config)
import backend.mcp.tools 

logger = logging.getLogger("api-gateway")

# CORS configs (Rule R4: Zero-Trust)
allowed_origins = [
    os.getenv("ADMIN_URL", "https://admin.smartshop.test"),
    os.getenv("API_URL", "https://api.smartshop.test"),
    os.getenv("APP_URL", "https://smartshop.test")
]
cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS")
if cors_origins_str:
    allowed_origins = [o.strip() for o in cors_origins_str.split(",")]

cors_config = CORSConfig(allow_origins=allowed_origins, allow_credentials=True)

# Application Instance
memory_store = MemoryStore()
rate_limit_config = RateLimitConfig(
    rate_limit=("minute", int(os.getenv("RATE_LIMIT_GLOBAL_MINUTE", "1000"))),
    exclude=["/health", "/metrics", "/schema"],
    store="memory_store"
)

app = Litestar(
    route_handlers=[
        IntentController, IntentStreamController, PulseStreamController,
        HealthController, MCPController, AuthController,
        NotificationController, AuditorController, UserController,
        CategoryController, ProductController, PublicProductController, ArticleController, OrderController,
        CheckoutController, ChatController, SettingsController, AIController, ContentController, MediaController, ContentStreamController,
        BannerController, stt_websocket, TTSController, IntentMapController, SchedulerController,
    ],
    middleware=[BodyLimitMiddleware, rate_limit_config.middleware, DomainGuardMiddleware, AuthMiddleware],
    cors_config=cors_config,
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
