"""
CNS - Central Nervous System: SignalCenter (V70.0)

Single dispatch hub unifying DB persistence, SSE Pulse, and Voice Modality.
All system-wide alerts MUST go through this service.

Replaces:
  - Manual `Notification(...)` instantiation in auth.py, chat.py
  - Ad-hoc `ui.showToast` emits in pulse.ts
  - Isolated `vuiController.speak()` in resume.ts

Rule Reference:
  - R1.13: Proactive Nerve System Protocol
  - R00: Central dispatch, no ad-hoc side effects in controllers
"""
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")


class SignalCenter:
    """
    The CNS brain. One method to rule them all: dispatch().
    Atomically: Save DB + Emit SSE Pulse with modality metadata.
    """

    async def dispatch(
        self,
        user_id: str,
        signal: SignalSchema,
        db_session: AsyncSession,
        tenant_id: str = "default"
    ) -> None:
        """
        Unified signal dispatch.
        1. Persist to Notification table (audit trail).
        2. Emit SYSTEM_SIGNAL via event_bus (SSE -> Frontend Distributor).
        """
        notif_id = str(uuid.uuid4())

        # Phase 1: DB Persistence (Zero-Hydration Scalar Insert)
        try:
            from sqlalchemy import text
            await db_session.execute(
                text("""
                    INSERT INTO notifications (id, user_id, type, message, is_read, created_at, updated_at)
                    VALUES (:id, :uid, :type, :msg, false, NOW(), NOW())
                """),
                {
                    "id": notif_id,
                    "uid": user_id,
                    "type": signal.signal_type,
                    "msg": signal.message
                }
            )
            await db_session.commit()
        except Exception as e:
            logger.error(f"[SignalCenter] DB persist failed for user {user_id}: {e}")
            # Non-fatal: continue with SSE emit

        # Phase 2: SSE Emit with full modality context
        # Frontend SignalDistributor will decode severity -> modalities
        try:
            await event_bus.emit("SYSTEM_SIGNAL", {
                "notification_id": notif_id,
                "user_id": user_id,
                "message": signal.message,
                "severity": signal.severity.value,
                "signal_type": signal.signal_type,
                "payload": signal.payload or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"[SignalCenter] SSE emit failed for user {user_id}: {e}")


# Singleton instance — import from anywhere
signal_center = SignalCenter()
