import os
from contextvars import ContextVar
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

logger = logging.getLogger("api-gateway")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# SQLite fallback for absolute certainty in tests if missing DB env
_URL = DATABASE_URL or "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"

engine = create_async_engine(
    _URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    echo=False
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Global contextvar to hold the current tenant ID for the request
current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)

async def connect_db():
    logger.info("Initializing SQLAlchemy Database Connection...")
    # Engine is lazy initialization, but we can emit a probe here if needed
    pass

async def disconnect_db():
    logger.info("Closing SQLAlchemy Database Engine...")
    await engine.dispose()
