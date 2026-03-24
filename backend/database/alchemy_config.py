import os
import logging
import orjson
from typing import Any
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

logger = logging.getLogger("api-gateway")

async def asyncpg_setup(conn: Any) -> None:
    """
    [CTO ELITE] Cấu hình asyncpg ở mức độ Native.
    1. Đưa orjson vào lõi để byte-to-JSON siêu tốc.
    2. Giới hạn cache để bảo vệ 2GB RAM.
    """
    # Đăng ký orjson cho JSON và JSONB
    await conn.set_type_codec(
        "json", encoder=orjson.dumps, decoder=orjson.loads, schema="pg_catalog"
    )
    await conn.set_type_codec(
        "jsonb", encoder=orjson.dumps, decoder=orjson.loads, schema="pg_catalog"
    )

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
        from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, AsyncSessionConfig
        self.litestar_config = SQLAlchemyAsyncConfig(
            engine_instance=self.get_engine(),
            create_all=False,
            session_config=AsyncSessionConfig(expire_on_commit=False)
        )

    def get_engine(self):
        if self._engine is None:
            engine_kwargs: dict[str, Any] = {
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
                        },
                        "on_connect": asyncpg_setup,
                    }
                })
                logger.info(f"[Database] Initializing Elite asyncpg engine (orjson enabled)")
                
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
