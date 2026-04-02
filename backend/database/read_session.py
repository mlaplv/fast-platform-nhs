"""
Read-Only Database Session Provider
=====================================
Provides a SQLAlchemy AsyncSession restricted to SELECT-only operations.
Used exclusively by the SUPPORT_NAME_CLIENT operative to enforce
infrastructure-level data access boundaries.

Pattern: Litestar Dependency Injection via `provide_read_only_db`.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")


@asynccontextmanager
async def _read_only_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession with autoflush=False and autocommit=False.
    Any write attempt (INSERT/UPDATE/DELETE) will raise an IntegrityError
    at the DB driver level since we never call session.commit().
    """
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Disable autoflush: prevents accidental writes from pending state
        session.sync_session.autoflush = False
        try:
            yield session
        except Exception:
            # Never commit — read-only guarantee
            await session.rollback()
            raise
        finally:
            await session.close()


async def provide_read_only_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Litestar DI provider for read-only DB access.
    Inject via: `db: AsyncSession = Dependency(provide_read_only_db)`
    """
    async with _read_only_session() as session:
        yield session
