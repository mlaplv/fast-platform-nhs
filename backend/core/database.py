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

# Fallback cho local (ưu tiên lấy từ biến môi trường của uv/Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/fast_platform")

db_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config={"expire_on_commit": False},
    engine_config={"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}
)

alchemy_plugin = SQLAlchemyPlugin(config=db_config)
