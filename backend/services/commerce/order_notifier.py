import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.event_bus import event_bus
from backend.services.core.zalo_service import zalo_service
from backend.database import async_session_maker
from backend.database.models import Order

logger = logging.getLogger("api-gateway")

async def handle_order_created(payload: dict) -> None:
    """
    Lắng nghe sự kiện Đơn hàng mới:
    1. Check xem số điện thoại khách hàng có Zalo không.
    2. Cập nhật vào Metadata của đơn hàng thưa sếp!
    """
    order_id = payload.get("id")
    phone = payload.get("phone")

    if not order_id or not phone:
        return

    logger.info(f"[OrderNotifier] Checking Zalo for Order {order_id} (Phone: {phone})")

    # 1. Phát hiện Zalo (Free technique)
    has_zalo = await zalo_service.check_existence(phone)

    # 2. Cập nhật Metadata vào DB
    async with async_session_maker() as db_session:
        try:
            stmt = select(Order).where(Order.id == order_id)
            res = await db_session.execute(stmt)
            order = res.scalar_one_or_none()

            if order:
                meta = dict(order.order_metadata or {})
                meta["zalo_status"] = "ACTIVE" if has_zalo else "NOT_FOUND"
                order.order_metadata = meta
                await db_session.commit()

                # [ELITE V2.2] Push Notification to Zalo Admin
                gift_info = meta.get("gift_info")
                await zalo_service.push_order_notification(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    total_amount=order.total_amount,
                    gift_info=gift_info if isinstance(gift_info, dict) else None
                )

                logger.info(f"[OrderNotifier] Updated Zalo status for {order_id}: {meta['zalo_status']}")
        except Exception as e:
            logger.error(f"[OrderNotifier] Failed to update Zalo status for {order_id}: {e}")

# Đăng ký lắng nghe sự kiện thưa sếp!
event_bus.subscribe("ORDER_CREATED", handle_order_created)
