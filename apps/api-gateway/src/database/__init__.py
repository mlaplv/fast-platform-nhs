import os
from contextvars import ContextVar
import logging
from .alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

# Global contextvar for tenant isolation
current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)

# Unified Exports
engine = alchemy_config.get_engine()
async_session_maker = alchemy_config.create_session_maker()

async def connect_db():
    logger.info("[Database] Connection pool initialized via AlchemyConfig.")

async def disconnect_db():
    logger.info("[Database] Disposing Engine...")
    await alchemy_config.get_engine().dispose()
