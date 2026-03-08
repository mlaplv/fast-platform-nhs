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
            async with self.session_maker() as session:
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

    async def handle_content_step_completed(self, payload: Dict[str, Any]):
        """Callback for CONTENT_STEP_COMPLETED event."""
        campaign_id = payload.get("campaign_id")
        step = payload.get("step")
        status = payload.get("status")
        tenant_id = payload.get("tenant_id", "default")
        data = payload.get("data", {})

        msg = f"Dạ sếp, em đã hoàn thành Bước {step}. Mời sếp xem kết quả và duyệt để em chạy tiếp ạ!"
        if step == 2:
            msg = f"Dạ sếp, em đã tìm xong bộ ảnh cho bài viết (Bước 2). Sếp chọn ảnh ưng ý để em lập dàn ý nhé!"
        elif step == 3:
            msg = f"Dạ sếp, dàn ý chi tiết (Bước 3) đã sẵn sàng. Sếp xem qua có cần chỉnh sửa gì không ạ?"
        elif step == 4:
            msg = f"Dạ sếp, em đã viết xong bản thảo (Bước 4). Sếp duyệt bài để em kiểm tra đạo văn nhé!"
        elif step == 6:
            msg = f"Chúc mừng sếp! Bài viết đã hoàn tất toàn bộ 6 bước và sẵn sàng xuất bản ạ."

        try:
            async with self.session_maker() as session:
                await session.execute(
                    text("""
                        INSERT INTO chat_messages (id, session_id, role, content, modality, tenant_id, created_at, updated_at)
                        VALUES (:id, 'account', 'assistant', :content, 'text', :tid, NOW(), NOW())
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "content": json.dumps({
                            "text": msg,
                            "category": "CONTENT_CREATE",
                            "campaign_id": campaign_id,
                            "step": step,
                            "status": status,
                            "keywords": data.get("keywords") if step == 2 else None,
                            "assets": data.get("assets") if step == 2 else None,
                            "outline": data.get("outline") if step == 3 else None,
                        }),
                        "tid": tenant_id
                    }
                )
                await session.commit()
            logger.info(f"[XoHiResponder] Proactive content log persisted for step {step}")
        except Exception as e:
            logger.error(f"[XoHiResponder] Content log persistence failed: {e}")

# Initialize and subscribe
xohi_responder = XoHiResponder()

def setup_subscriptions():
    """Register all proactive sensors."""
    event_bus.subscribe("ORDER_CREATED", xohi_responder.handle_order_created)
    event_bus.subscribe("ORDER_CANCELLED", xohi_responder.handle_order_cancelled)
    event_bus.subscribe("CONTENT_STEP_COMPLETED", xohi_responder.handle_content_step_completed)
    logger.info("[XoHiResponder] Subscriptions initialized.")
