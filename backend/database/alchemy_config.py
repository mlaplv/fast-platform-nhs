import os
import logging
from typing import cast, Optional, Callable
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig as BaseSQLAlchemyAsyncConfig, AsyncSessionConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy import event, select
from backend.core.database import is_system_read_only
from litestar.exceptions import PermissionDeniedException
from advanced_alchemy.extensions.litestar._utils import get_aa_scope_state, set_aa_scope_state
from advanced_alchemy.routing.context import reset_routing_context
from litestar.datastructures import State
from litestar.types import Scope

import time
from datetime import datetime, timezone

logger = logging.getLogger("api-gateway")

# [SOC Monitor V2.3] In-memory counters — zero overhead (no I/O, no network).
# Tự động tích lũy từ event listeners sẵn có, luôn ON nhưng không tốn tài nguyên.
_DB_STATS: dict = {
    "leak_count": 0,                  # Tổng số lần connection giữ quá 10s
    "last_leak_duration_ms": 0,       # Duration của leak gần nhất
    "last_leak_time": None,           # ISO timestamp
    "slow_query_count": 0,            # Tổng số query chậm > 1s
    "last_slow_query_sql": "",        # 200 ký tự đầu
    "last_slow_query_duration_ms": 0, # Duration ms
    "last_slow_query_time": None,     # ISO timestamp
}

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
                # [OPT V2.3] Single Uvicorn worker — pool_size=8 là đủ.
                # Concurrent DB ops thực tế hiếm khi vượt 6-8 với 1 worker.
                # Giảm từ pool_size=12+overflow=8 (max 20) → 8+4 (max 12)
                # Tiết kiệm ~4 idle asyncpg connections × ~4MB = ~16MB RAM.
                engine_kwargs.update({
                    "pool_size": 8,
                    "max_overflow": 4,
                    "pool_timeout": 10,
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                    "pool_reset_on_return": "rollback",
                    "connect_args": {
                        "command_timeout": 30,
                        "server_settings": {
                            "jit": "off",
                            "application_name": "fast-platform-v2.3",
                        }
                    }
                })
                logger.info("[Database] Initializing asyncpg engine: pool_size=8, max_overflow=4, pool_timeout=10")
                
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
    if is_system_read_only():
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
            # [SOC Monitor] Tích lũy để expose qua /health/db
            _DB_STATS["slow_query_count"] += 1
            _DB_STATS["last_slow_query_sql"] = statement[:200]
            _DB_STATS["last_slow_query_duration_ms"] = int(total * 1000)
            _DB_STATS["last_slow_query_time"] = datetime.now(timezone.utc).isoformat()

from sqlalchemy.pool import Pool
import traceback

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Ghi nhận thời điểm connection được lấy ra khỏi pool để phục vụ phát hiện rò rỉ (leak)."""
    connection_record.info["checkout_time"] = time.perf_counter()
    connection_record.info["checkout_traceback"] = "".join(traceback.format_stack())

@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Tính toán và cảnh báo nếu connection bị chiếm giữ quá lâu (ngưy cơ leak)."""
    checkout_time = connection_record.info.get("checkout_time")
    if checkout_time:
        duration = time.perf_counter() - checkout_time
        if duration > 10.0:
            tb = connection_record.info.get("checkout_traceback", "No traceback captured.")
            logger.warning(
                f"⚠️ [CONNECTION_LEAK_WARNING] Connection checkout duration: {duration:.4f}s!\n"
                f"Checkout Traceback:\n{tb}"
            )
            # [SOC Monitor] Tích lũy để expose qua /health/db
            _DB_STATS["leak_count"] += 1
            _DB_STATS["last_leak_duration_ms"] = int(duration * 1000)
            _DB_STATS["last_leak_time"] = datetime.now(timezone.utc).isoformat()
