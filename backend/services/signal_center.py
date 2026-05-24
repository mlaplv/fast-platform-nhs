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
        """
        notif_id = str(uuid.uuid4())

        # Phase 1: DB Persistence (Elite V2.2: Conditional Persistence Guard)
        should_persist = signal.persist
        if should_persist is None:
            # Default behavior: CRITICAL/ACTION = True, INFO/PROGRESS = False
            should_persist = signal.severity in [SignalSeverity.CRITICAL, SignalSeverity.ACTION]

        if should_persist:
            try:
                from backend.database.models import Notification
                import json
                db_message = signal.message
                if signal.payload:
                    db_message = f"{signal.message} |metadata:{json.dumps(signal.payload)}"
                
                notif = Notification(
                    id=notif_id,
                    user_id=user_id,
                    type=signal.signal_type,
                    message=db_message,
                    is_read=False,
                )
                db_session.add(notif)
                # V70.3 Explicit Commit to bypass Autocommit uncertainties
                await db_session.commit()
            except Exception as e:
                logger.error(f"[SignalCenter] DB persist failed for user {user_id}: {e}")
                # Non-fatal: continue with SSE emit
        else:
            logger.debug(f"[SignalCenter] Noise-Gate: Bypassed DB persistence for {signal.severity} signal.")

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
