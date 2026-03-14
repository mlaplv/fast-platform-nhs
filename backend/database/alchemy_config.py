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
        self.db_url = os.getenv("DATABASE_URL")
        if self.db_url and self.db_url.startswith("postgresql://"):
            self.db_url = self.db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        self._url = self.db_url or "sqlite+aiosqlite:///:memory:"
        
        # Plugin Config for Litestar
        from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, AsyncSessionConfig
        self.litestar_config = SQLAlchemyAsyncConfig(
            connection_string=self._url,
            create_all=False,
            session_config=AsyncSessionConfig(expire_on_commit=False)
        )
        
        self._engine = None
        self._session_maker = None

    def get_engine(self):
        if self._engine is None:
            engine_kwargs = {
                "echo": False,
                "pool_recycle": 3600,
            }
            # Rule: Only add pooling for Postgres (SQLite uses StaticPool)
            if self._url.startswith("postgresql"):
                engine_kwargs["pool_size"] = 10
                engine_kwargs["max_overflow"] = 10
                engine_kwargs["pool_pre_ping"] = True
                engine_kwargs["pool_recycle"] = 300
                
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
