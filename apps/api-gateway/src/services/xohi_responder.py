import logging
import uuid
from typing import Dict, Any
from sqlalchemy import text
from src.services.event_bus import event_bus
from src.database import alchemy_config

logger = logging.getLogger("api-gateway")

class XoHiResponder:
    """
    R23: Proactive Nerve System Responder.
    Listens to the EventBus and reacts instantly to critical system events.
    """
    def __init__(self):
        self.session_maker = alchemy_config.create_session_maker()

    async def handle_order_created(self, payload: Dict[str, Any]):
        """Callback for ORDER_CREATED event."""
        order_id = payload.get("id")
        customer = payload.get("customer", "Khách lạ")
        is_spam = payload.get("is_spam", False)
        tenant_id = payload.get("tenant_id")
        
        # 1. Immediate Notification
        msg = f"Đơn hàng mới từ {customer} (ID: {order_id[:8]})"
        if is_spam:
            msg = f"🚩 CẢNH BÁO SPAM: {msg} - Đã tự động gắn tag SPAM."
        
        await self._push_notification(
            tenant_id=tenant_id,
            msg=msg,
            severity="info" if not is_spam else "critical"
        )
        logger.info(f"[XoHiResponder] Handled ORDER_CREATED: {order_id}")

    async def handle_order_cancelled(self, payload: Dict[str, Any]):
        """Callback for ORDER_CANCELLED event."""
        order_id = payload.get("id")
        reason = payload.get("reason", "Không rõ lý do")
        tenant_id = payload.get("tenant_id")
        
        msg = f"Khách đã HỦY đơn {order_id[:8]}. Lý do: {reason}"
        await self._push_notification(tenant_id=tenant_id, msg=msg, severity="warning")
        logger.info(f"[XoHiResponder] Handled ORDER_CANCELLED: {order_id}")

    async def _push_notification(self, tenant_id: str, msg: str, severity: str):
        """Save notification directly via Zero-ORM snippet."""
        try:
            async with self.session_maker() as session:
                await session.execute(
                    text("""
                        INSERT INTO notifications (id, type, message, is_read, tenant_id, created_at, updated_at)
                        VALUES (:id, :type, :msg, false, :tid, NOW(), NOW())
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "type": severity,
                        "msg": msg,
                        "tid": tenant_id
                    }
                )
                await session.commit()
        except Exception as e:
            logger.error(f"[XoHiResponder] Notification push failed: {e}")

# Initialize and subscribe
xohi_responder = XoHiResponder()

def setup_subscriptions():
    """Register all proactive sensors."""
    event_bus.subscribe("ORDER_CREATED", xohi_responder.handle_order_created)
    event_bus.subscribe("ORDER_CANCELLED", xohi_responder.handle_order_cancelled)
    logger.info("[XoHiResponder] Subscriptions initialized.")
