import logging
import uuid
from typing import Dict, Union, Optional
from sqlalchemy import text
from backend.services.event_bus import event_bus
import json
from backend.database import alchemy_config

logger = logging.getLogger("api-gateway")

class XoHiResponder:
    """
    R23: Proactive Nerve System Responder.
    Listens to the EventBus and reacts instantly to critical system events.
    """
    def __init__(self):
        self.session_maker = alchemy_config.create_session_maker()

    async def handle_order_created(self, payload: Dict[str, object]):
        """Callback for ORDER_CREATED event. Marks spam and notifies admins."""
        order_id = payload.get("id")
        ip = payload.get("ip", "unknown")
        ua = payload.get("user_agent", "unknown")
        tenant_id = payload.get("tenant_id")
        total_amount = payload.get("total_amount", 0.0)
        phone = payload.get("phone", "unspecified")
        address = payload.get("address", "")
        
        # 1. Anti-Spam Check (Proactive Defense)
        from backend.services.anti_spam import anti_spam_service as anti_spam
        from backend.services.xohi_memory import xohi_memory
        
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

    async def handle_order_cancelled(self, payload: Dict[str, object]):
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

    async def handle_content_step_completed(self, payload: Dict[str, object]):
        """Callback for CONTENT_STEP_COMPLETED event."""
        campaign_id = payload.get("campaign_id")
        user_id = payload.get("user_id")
        step = payload.get("step")
        status = payload.get("status")
        tenant_id = payload.get("tenant_id", "default")
        data = payload.get("data", {})

        msg = f"[Content] Hoàn thành Bước {step}. Đang chờ sếp duyệt."
        if step == 2:
            msg = f"[Content] Đã tìm xong bộ ảnh (Bước 2). Mời sếp chọn."
        elif step == 3:
            msg = f"[Content] Đàn ý Bước 3 đã sẵn sàng."
        elif step == 4:
            msg = f"[Content] Bản thảo Bước 4 đã hoàn tất."
        elif step == 6:
            msg = f"✨ Bài viết đã hoàn thành 6 bước. Sẵn sàng xuất bản!"

        try:
            async with self.session_maker() as session:
                # Slim Log: Only store the audit trail, NOT the raw payload.
                # Full data (keywords, assets, outline) lives in content_campaigns table.
                # Frontend fetches via GET /api/v1/content/campaigns/{id} on Resume.
                content_payload = {
                    "text": msg,
                    "category": "CONTENT_CREATE",
                    "campaign_id": campaign_id,
                    "step": step,
                    "status": status,
                }

                # Plan D: UPSERT — Find existing record for this campaign+step, update it.
                # This prevents data loss if sếp F5s during the async window between
                # the SSE signal and the DB write completing.
                result = await session.execute(
                    text("""
                        SELECT id FROM chat_messages
                        WHERE session_id = 'account'
                        AND user_id = :uid
                        AND content->>'category' = 'CONTENT_CREATE'
                        AND content->>'campaign_id' = :cid
                        AND content->>'step' = :step
                        ORDER BY created_at DESC LIMIT 1
                    """),
                    {"uid": user_id, "cid": campaign_id, "step": str(step)}
                )
                existing_row = result.fetchone()

                if existing_row:
                    # UPDATE existing record — idempotent, safe to run multiple times
                    await session.execute(
                        text("UPDATE chat_messages SET content = :content, updated_at = NOW() WHERE id = :id"),
                        {"content": json.dumps(content_payload), "id": existing_row[0]}
                    )
                    logger.info(f"[XoHiResponder] UPSERT → UPDATED step {step} log for campaign {campaign_id}")
                else:
                    # INSERT new record
                    await session.execute(
                        text("""
                            INSERT INTO chat_messages (id, session_id, user_id, role, content, modality, tenant_id, created_at, updated_at)
                            VALUES (:id, 'account', :uid, 'assistant', :content, 'text', :tid, NOW(), NOW())
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "uid": user_id,
                            "content": json.dumps(content_payload),
                            "tid": tenant_id
                        }
                    )
                    logger.info(f"[XoHiResponder] UPSERT → INSERTED step {step} log for campaign {campaign_id}")

                await session.commit()
        except Exception as e:
            logger.error(f"[XoHiResponder] Content log persistence failed: {e}")

    async def handle_content_progress(self, payload: Dict[str, object]):
        """Callback for CONTENT_PROGRESS event. Progress is ephemeral — no DB write."""
        # Progress ticks are real-time signals only (streamed via SSE/Pulse).
        # They are NOT worth storing to DB — high frequency, low value, large volume.
        # Only CONTENT_STEP_COMPLETED events are worth persisting as audit trail.
        campaign_id = payload.get("campaign_id")
        step = payload.get("step")
        msg = payload.get("message", "")
        logger.debug(f"[XoHiResponder] Progress (no DB write): campaign={campaign_id} step={step} msg={msg[:60]}")

# Initialize and subscribe
xohi_responder = XoHiResponder()

def setup_subscriptions():
    """Register all proactive sensors."""
    event_bus.subscribe("ORDER_CREATED", xohi_responder.handle_order_created)
    event_bus.subscribe("ORDER_CANCELLED", xohi_responder.handle_order_cancelled)
    event_bus.subscribe("CONTENT_STEP_COMPLETED", xohi_responder.handle_content_step_completed)
    event_bus.subscribe("CONTENT_PROGRESS", xohi_responder.handle_content_progress)
    logger.info("[XoHiResponder] Subscriptions initialized.")
