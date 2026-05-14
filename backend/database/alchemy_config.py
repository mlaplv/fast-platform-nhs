import os
import logging
from typing import cast, Optional, Callable
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig as BaseSQLAlchemyAsyncConfig, AsyncSessionConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy import event, select
from backend.core.database import SYSTEM_READ_ONLY
from litestar.exceptions import PermissionDeniedException
from advanced_alchemy.extensions.litestar._utils import get_aa_scope_state, set_aa_scope_state
from advanced_alchemy.routing.context import reset_routing_context
from litestar.datastructures import State
from litestar.types import Scope

import time
logger = logging.getLogger("api-gateway")

class EliteSQLAlchemyAsyncConfig(BaseSQLAlchemyAsyncConfig):
    """
    R1.5 Elite Configuration: Resolves library deprecations at the root.
    """
    def provide_session(self, state: State, scope: Scope) -> AsyncSession:
        # Override to remove deprecated 'advanced_alchemy._listeners.set_async_context' call
        session: Optional[AsyncSession] = cast(Optional[AsyncSession], get_aa_scope_state(scope, self.session_scope_key))
        if session is None:
            reset_routing_context()
            session_maker: Callable[[], AsyncSession] = cast(Callable[[], AsyncSession], state[self.session_maker_app_state_key])
            session = session_maker()
            set_aa_scope_state(scope, self.session_scope_key, session)
        return session

class AlchemyConfig:
    """
    R1.5 Unified Database Engine Management.
    """
    _engine: Optional[AsyncEngine] = None
    _session_maker: Optional[async_sessionmaker[AsyncSession]] = None
    db_url: Optional[str] = None
    _url: str = ""
    litestar_config: EliteSQLAlchemyAsyncConfig

    def __init__(self) -> None:
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

    def get_engine(self) -> AsyncEngine:
        if self._engine is None:
            engine_kwargs: dict[str, object] = {
                "echo": False,
                "pool_recycle": 3600,
            }
            # Rule: Only add pooling for Postgres (SQLite uses StaticPool)
            if self._url.startswith("postgresql"):
                # [Elite V2.2] Optimized pooling for 2GB RAM VPS
                engine_kwargs.update({
                    "pool_size": 8,
                    "max_overflow": 10,
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

    def create_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            self._session_maker = async_sessionmaker(
                self.get_engine(), 
                expire_on_commit=False, 
                class_=AsyncSession
            )
        return self._session_maker

# Singleton instance
alchemy_config = AlchemyConfig()

from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute", retval=True)
def before_cursor_execute(conn, cursor, statement, parameters, context, execmany):
    # [THIẾT QUÂN LUẬT] Chặn Query mutation ở tầng driver nếu phong tỏa
    if SYSTEM_READ_ONLY:
        forbidden_words = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER"]
        stmt_upper = statement.upper()
        if any(word in stmt_upper for word in forbidden_words):
            allowed_tables = ["audit_logs", "drafts", "notifications", "chat_messages"]
            if not any(tbl in statement.lower() for tbl in allowed_tables):
                logger.error(f"🛑 [MARTIAL_LAW] Low-level block on statement: {statement[:100]}...")
                raise PermissionDeniedException("Hệ thống đang trong trạng thái PHONG TỎA DB. Mọi truy vấn thay đổi bị cấm.")

    context._query_start_time = time.perf_counter()
    return statement, parameters

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, execmany):
    if hasattr(context, "_query_start_time"):
        total = time.perf_counter() - context._query_start_time
        if total > 1.0:
            logger.warning(f"⚠️ [SLOW_QUERY] Duration: {total:.4f}s | SQL: {statement}")
