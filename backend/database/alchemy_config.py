import os
import logging
from typing import cast, Optional, Callable
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig as BaseSQLAlchemyAsyncConfig, AsyncSessionConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from advanced_alchemy.extensions.litestar._utils import get_aa_scope_state, set_aa_scope_state
from advanced_alchemy.routing.context import reset_routing_context
from litestar.datastructures import State
from litestar.types import Scope

logger = logging.getLogger("api-gateway")

class EliteSQLAlchemyAsyncConfig(BaseSQLAlchemyAsyncConfig):
    """
    R1.5 Elite Configuration: Resolves library deprecations at the root.
    """
    def provide_session(self, state: State, scope: Scope) -> AsyncSession:
        # Override to remove deprecated 'advanced_alchemy._listeners.set_async_context' call
        session = cast("Optional[AsyncSession]", get_aa_scope_state(scope, self.session_scope_key))
        if session is None:
            reset_routing_context()
            session_maker = cast("Callable[[], AsyncSession]", state[self.session_maker_app_state_key])
            session = session_maker()
            set_aa_scope_state(scope, self.session_scope_key, session)
        return session

class AlchemyConfig:
    """
    R1.5 Unified Database Engine Management.
    """
    def __init__(self):
        self._engine = None
        self._session_maker = None
        self.db_url = os.getenv("DATABASE_URL")
        if self.db_url and self.db_url.startswith("postgresql://"):
            self.db_url = self.db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        self._url = self.db_url or "sqlite+aiosqlite:///:memory:"
        
        # Plugin Config for Litestar - R1.5: Pass the shared engine instance
        self.litestar_config = EliteSQLAlchemyAsyncConfig(
            engine_instance=self.get_engine(),
            create_all=False,
            session_config=AsyncSessionConfig(expire_on_commit=False)
        )

    def get_engine(self):
        if self._engine is None:
            engine_kwargs: dict[str, object] = {
                "echo": False,
                "pool_recycle": 3600,
            }
            # Rule: Only add pooling for Postgres (SQLite uses StaticPool)
            if self._url.startswith("postgresql"):
                # [Elite V2.2] Optimized pooling for 2GB RAM VPS
                engine_kwargs.update({
                    "pool_size": 5,
                    "max_overflow": 5,
                    "pool_timeout": 30,
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                    # [PHASE 8] Truyền cấu hình chuyên sâu xuống asyncpg
                    "connect_args": {
                        "command_timeout": 30,
                        "server_settings": {
                            "jit": "off", # Tắt JIT để tiết kiệm RAM cho Postgres
                            "application_name": "fast-platform-v2.2",
                        }
                    }
                })
                logger.info(f"[Database] Initializing Elite asyncpg engine")
                
            self._engine = create_async_engine(self._url, **engine_kwargs)
        return self._engine

    def create_session_maker(self):
        if self._session_maker is None:
            self._session_maker = async_sessionmaker(
                self.get_engine(), 
                expire_on_commit=False, 
                class_=AsyncSession
            )
        return self._session_maker

# Singleton instance
alchemy_config = AlchemyConfig()
