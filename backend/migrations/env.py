import asyncio
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

# [Elite V2.2] Tự động nạp .env để lấy DATABASE_URL chuẩn
load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../.env')))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Thêm root dự án vào sys.path để import được module backend
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Base chứa MetaData của dự án
from backend.database.models import Base

# Object config của Alembic
config = context.config

# Cấu hình logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """Lấy Database URL từ environment (.env)"""
    return os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

def include_object(object, name, type_, reflected, compare_to):
    """
    [MASTER LEVEL] Chiến thuật chặn đứng OOM từ trong trứng nước.
    1. Chỉ quét bảng nằm trong MetaData dự án.
    2. Bỏ qua hoàn toàn các bảng hệ thống, schema ngoại lai.
    3. Giảm thiểu tối đa việc phản chiếu (reflection) dữ liệu ko cần thiết.
    """
    # 1. Chặn schema rác (cực kỳ quan trọng với Postgres/PostGIS)
    if hasattr(object, "schema") and object.schema is not None and object.schema != "public":
        return False
        
    # 2. Chỉ cho lọc bảng nội bộ
    if type_ == "table":
        # So sánh tên bảng trực tiếp để tránh nạp Object Table vào RAM
        return name in target_metadata.tables
        
    # 3. Chặn các index/constraint không liên quan
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        include_schemas=False,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Cấu hình Context đẳng cấp Master: Chống Reflection Bloat"""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=False,
        compare_server_default=False,
        include_object=include_object,
        include_schemas=False,         # Master Fix: Không quét đa schema
        render_as_batch=True,
        # Tối ưu hóa việc nạp metadata
        reflection_options={
            "skip_nested": True,      # Không nạp quan hệ lồng nhau khi quét
        }
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Thực thi migration theo luồng Async Native"""
    url = get_url()
    
    # Khởi tạo engine với NullPool để giải phóng RAM ngay sau khi xong
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Chạy migration online thông qua asyncio loop"""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
