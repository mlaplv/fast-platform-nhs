import os
import logging
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

logger = logging.getLogger("api-gateway")

class AlchemyConfig:
    """
    R1.5 Unified Database Engine Management.
    Centralizes engine and session maker creation to prevent duplicate engines and import errors.
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
            engine_kwargs = {
                "echo": False,
                "pool_recycle": 3600,
            }
            # Rule: Only add pooling for Postgres (SQLite uses StaticPool)
            if self._url.startswith("postgresql"):
                # R1.5 Improved pooling for High-Concurrency Agent Flows
                engine_kwargs["pool_size"] = 20        # Increase from 10
                engine_kwargs["max_overflow"] = 20     # Increase from 10
                engine_kwargs["pool_timeout"] = 60      # Default is 30
                engine_kwargs["pool_pre_ping"] = True
                engine_kwargs["pool_recycle"] = 300
                logger.info(f"[Database] Initializing engine with shared pool (size: 20, overflow: 20)")
                
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
