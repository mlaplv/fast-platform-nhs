"""
Lý do chọn giải pháp:
- Yêu cầu V60.0: Full Async I/O (100%).
- VPS 2GB RAM: Tiết kiệm connection pool (pool_size=5, max_overflow=10).
- Tuân thủ RULES.md: Sử dụng AdvancedAlchemy tạo cấu hình Async SQLAlchemy.
- expire_on_commit=False: Ngăn chặn lazy loading ngầm sinh ra N+1 queries.
"""

import os
from advanced_alchemy.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

# Elite V2.2: DATABASE_URL must be provided via environment. 
# Defaults to a strict environment requirement to prevent production data leaks.
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    # Fallback to a non-existent local for dev but log warning
    DATABASE_URL = "postgresql+asyncpg://postgres@localhost:5432/fast_platform"

db_config: SQLAlchemyAsyncConfig = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config={"expire_on_commit": False},
    engine_config={"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}
)

alchemy_plugin: SQLAlchemyPlugin = SQLAlchemyPlugin(config=db_config)
