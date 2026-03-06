import logging
import uuid
from typing import Dict, Any
from sqlalchemy import text
from src.services.event_bus import event_bus
import json
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
        """Callback for ORDER_CREATED event. Marks spam and notifies admins."""
        order_id = payload.get("id")
        ip = payload.get("ip", "unknown")
        ua = payload.get("user_agent", "unknown")
        tenant_id = payload.get("tenant_id")
        total_amount = payload.get("total_amount", 0.0)
        phone = payload.get("phone", "unspecified")
        address = payload.get("address", "")
        
        # 1. Anti-Spam Check (Proactive Defense)
        from src.services.anti_spam import anti_spam_service as anti_spam
        from src.services.xohi_memory import xohi_memory
        
        # Read Campaign Mode from Redis
        campaign_flag = await xohi_memory.client.get("system:campaign_mode")
        is_campaign_mode = (campaign_flag == b"1")

        is_spam, reason, score, fingerprint = await anti_spam.check_order_spam(
            ip, ua, tenant_id, 
            {"total": total_amount, "phone": phone, "address": address, "items": payload.get("items", [])},
            is_campaign_mode=is_campaign_mode
        )
        
        if is_spam:
            logger.warning(f"[Anti-Spam Shield] Detect SPAM order {order_id}: {reason}")
            # Mark it in DB instantly
            async with self.session_maker() as session:
                await session.execute(
                    text("UPDATE orders SET is_spam = true, spam_score = :score, fingerprint = :fp, spam_reason = :reason WHERE id = :id"),
                    {"score": score, "id": order_id, "fp": fingerprint, "reason": reason}
                )
                await session.commit()
        
        # 2. Immediate Notification
        customer = payload.get("customer", "Khách lạ")
        severity = "info"
        msg = f"Đơn hàng mới từ {customer} (ID: {order_id[:8]})"
        
        if is_spam:
            if score >= 90:
                severity = "critical"
                msg = f"🚨 RED ALERT: Phát hiện tấn công Click-Fraud cực mạnh! Đơn {order_id[:8]} đã bị cô lập hoàn toàn. Lý do: {reason}"
            else:
                severity = "warning"
                msg = f"🚩 CẢNH BÁO SPAM: {msg} - {reason}"
        
        await self._push_notification(
            tenant_id=tenant_id,
            msg=msg,
            severity=severity
        )

        # 3. Security Audit to XoHi Log (Nanobot Console)
        # R26: Persist as assistant message in 'account' session to ensure visibility for current user
        if is_spam:
            await self._persist_xohi_log(
                tenant_id=tenant_id,
                msg=msg,
                order_id=order_id,
                score=score
            )

        logger.info(f"[XoHiResponder] Handled ORDER_CREATED: {order_id} (is_spam={is_spam})")

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

    async def _persist_xohi_log(self, tenant_id: str, msg: str, order_id: str, score: float):
        """Persist security alert to ChatMessage history for XoHi console visibility."""
        try:
            # We target session_id='account' which is the default for user-specific logs in frontend
            # In a multi-user system, we might want to target specific admin user_ids
            # For now, following 'account' session pattern from ChatController
            async with self.session_maker() as session:
                # Get the first admin user to associate the log with (optional but better for consistency)
                # If no user_id, it will still show up if frontend filters by session_id='account'
                await session.execute(
                    text("""
                        INSERT INTO chat_messages (id, session_id, role, content, modality, tenant_id, created_at, updated_at)
                        VALUES (:id, 'account', 'assistant', :content, 'text', :tid, NOW(), NOW())
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "content": json.dumps({
                            "text": msg,
                            "info_type": "security_alert",
                            "order_id": order_id,
                            "spam_score": score
                        }),
                        "tid": tenant_id
                    }
                )
                await session.commit()
            logger.debug(f"[XoHiResponder] Security log persisted to ChatMessage history")
        except Exception as e:
            logger.error(f"[XoHiResponder] XoHi log persistence failed: {e}")

# Initialize and subscribe
xohi_responder = XoHiResponder()

def setup_subscriptions():
    """Register all proactive sensors."""
    event_bus.subscribe("ORDER_CREATED", xohi_responder.handle_order_created)
    event_bus.subscribe("ORDER_CANCELLED", xohi_responder.handle_order_cancelled)
    logger.info("[XoHiResponder] Subscriptions initialized.")
