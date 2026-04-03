import asyncio
import logging
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy import select, update
from backend.database import async_session_maker
from backend.database.models.media import MediaRegistry, MediaUsage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

async def migrate_media_usage():
    """
    Elite V2.2: Chuyển đổi dữ liệu từ 1-1 (legacy) sang Many-to-Many.
    Quét cột linked_post_id và tạo bản ghi tương ứng trong MediaUsage.
    """
    logger.info("🚀 Bắt đầu quá trình Neural Media Data Migration...")
    
    async with async_session_maker() as session:
        # 1. Tìm tất cả các ảnh có linked_post_id (Dữ liệu cũ)
        # Lưu ý: Cần kiểm tra xem model MediaRegistry có thuộc tính này không (đã được giữ lại qua migration v600)
        # Nếu đã xóa, ta sẽ phải dùng bảng alembic_version để xác định hoặc bỏ qua nếu là DB mới hoàn toàn.
        try:
            stmt = select(MediaRegistry).where(sa.text("linked_post_id IS NOT NULL"))
        except:
            # Dự phòng nếu SQLAlchemy model đã bỏ field này
            from sqlalchemy import text
            stmt = select(MediaRegistry).filter(text("linked_post_id IS NOT NULL"))
            
        res = await session.execute(stmt)
        assets = res.scalars().all()
        
        count = 0
        for asset in assets:
            # Lấy thông tin từ cột legacy
            # (Chúng ta truy cập trực tiếp qua __dict__ hoặc getattr để tránh lỗi attr nếu model đã bị refactor)
            lp_id = getattr(asset, 'linked_post_id', None)
            lp_type = getattr(asset, 'linked_post_type', 'unknown')
            
            if not lp_id:
                continue
                
            # 2. Tạo bản ghi MediaUsage mới (Many-to-Many)
            usage = MediaUsage(
                id=str(uuid4()),
                asset_id=asset.id,
                entity_id=lp_id,
                entity_type=lp_type or 'unknown',
                tenant_id=asset.tenant_id
            )
            session.add(usage)
            
            # 3. Cập nhật flag is_linked
            asset.is_linked = True
            count += 1
            
        await session.commit()
        logger.info(f"✅ Đã chuyển đổi thành công {count} liên kết sang Many-to-Many.")
        
        # 4. Neural Sync: Cập nhật is_linked cho tất cả các ảnh còn lại dựa trên bảng MediaUsage
        # (Đảm bảo tính nhất quán sau khi gieo mầm dữ liệu seed)
        logger.info("📡 Đang đồng bộ hóa trạng thái is_linked toàn hệ thống...")
        
        # Cập nhật is_linked = True cho những ảnh có trong MediaUsage
        subquery = select(MediaUsage.asset_id).scalar_subquery()
        await session.execute(
            update(MediaRegistry)
            .where(MediaRegistry.id.in_(subquery))
            .values(is_linked=True)
        )
        
        # Cập nhật is_linked = False cho những ảnh KHÔNG có trong MediaUsage
        await session.execute(
            update(MediaRegistry)
            .where(MediaRegistry.id.not_in(subquery))
            .values(is_linked=False)
        )
        
        await session.commit()
        logger.info("🏁 Quá trình đồng bộ hoàn tất (Neural Media Linker Active).")

if __name__ == "__main__":
    asyncio.run(migrate_media_usage())
