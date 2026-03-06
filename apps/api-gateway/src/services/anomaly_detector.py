"""
Anomaly Detector — Lightweight scalar-only anomaly scanning.
============================================================
V56.0 Phase 3: Autonomous Heartbeat.

Rules:
- ZERO ORM hydration (Rule 1.5) — scalar queries only
- < 10ms per query (Rule 1.8)
- Generates Notification records when anomalies detected
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")

# Alert threshold: spike factor over baseline (configurable via env in future)
SPIKE_THRESHOLD = 2.0
# Minimum baseline count to avoid false positives on low-volume stores
MIN_BASELINE_COUNT = 3


class AnomalyDetector:
    """
    Scalar-only anomaly detection. CẤM load ORM objects.
    Compares recent metrics vs historical baseline to detect spikes.
    """

    async def scan(self, session: AsyncSession, tenant_id: str = "default") -> List[Dict[str, Any]]:
        """
        Run all anomaly checks. Returns list of alerts.
        Each alert: {type, severity, message, data}
        """
        alerts: List[Dict[str, Any]] = []

        try:
            cancelled_alert = await self._check_cancelled_orders(session, tenant_id)
            if cancelled_alert:
                alerts.append(cancelled_alert)
        except Exception as e:
            logger.warning(f"[AnomalyDetector] cancelled_orders check failed: {e}")

        try:
            volume_alert = await self._check_order_volume(session, tenant_id)
            if volume_alert:
                alerts.append(volume_alert)
        except Exception as e:
            logger.warning(f"[AnomalyDetector] order_volume check failed: {e}")

        try:
            revenue_alert = await self._check_revenue_anomaly(session, tenant_id)
            if revenue_alert:
                alerts.append(revenue_alert)
        except Exception as e:
            logger.warning(f"[AnomalyDetector] revenue check failed: {e}")

        if alerts:
            await self._persist_alerts(session, alerts, tenant_id)
            logger.info(f"[AnomalyDetector] {len(alerts)} anomalies detected and persisted.")
        else:
            logger.debug("[AnomalyDetector] Scan complete — no anomalies.")

        return alerts

    async def _check_cancelled_orders(self, session: AsyncSession, tenant_id: str) -> Dict[str, Any] | None:
        """Compare cancelled orders last 1h vs 7-day hourly average."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        seven_days_ago = now - timedelta(days=7)

        # Count cancellations in last hour
        recent = await session.scalar(
            text("""
                SELECT COUNT(*) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND status = 'CANCELLED' AND updated_at >= :since
            """),
            {"tid": tenant_id, "since": one_hour_ago}
        ) or 0

        # Average hourly cancellations over 7 days
        total_7d = await session.scalar(
            text("""
                SELECT COUNT(*) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND status = 'CANCELLED' AND updated_at >= :since
            """),
            {"tid": tenant_id, "since": seven_days_ago}
        ) or 0

        baseline_hourly = total_7d / (7 * 24) if total_7d > 0 else 0

        if recent >= MIN_BASELINE_COUNT and baseline_hourly > 0 and recent > baseline_hourly * SPIKE_THRESHOLD:
            return {
                "type": "cancelled_spike",
                "severity": "WARNING",
                "message": f"⚠️ Đơn hủy tăng đột biến: {recent} đơn trong 1h qua (trung bình {baseline_hourly:.1f}/h).",
                "data": {"recent": recent, "baseline": round(baseline_hourly, 2)}
            }
        return None

    async def _check_order_volume(self, session: AsyncSession, tenant_id: str) -> Dict[str, Any] | None:
        """Compare new order volume last 1h vs 7-day hourly average."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        seven_days_ago = now - timedelta(days=7)

        recent = await session.scalar(
            text("""
                SELECT COUNT(*) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND created_at >= :since
            """),
            {"tid": tenant_id, "since": one_hour_ago}
        ) or 0

        total_7d = await session.scalar(
            text("""
                SELECT COUNT(*) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND created_at >= :since
            """),
            {"tid": tenant_id, "since": seven_days_ago}
        ) or 0

        baseline_hourly = total_7d / (7 * 24) if total_7d > 0 else 0

        if recent >= MIN_BASELINE_COUNT and baseline_hourly > 0 and recent > baseline_hourly * SPIKE_THRESHOLD:
            return {
                "type": "order_volume_spike",
                "severity": "INFO",
                "message": f"📈 Đơn hàng mới bất thường: {recent} đơn trong 1h qua (trung bình {baseline_hourly:.1f}/h).",
                "data": {"recent": recent, "baseline": round(baseline_hourly, 2)}
            }
        return None

    async def _check_revenue_anomaly(self, session: AsyncSession, tenant_id: str) -> Dict[str, Any] | None:
        """Compare today's revenue vs yesterday same hour."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_same_hour = yesterday_start + timedelta(hours=now.hour)

        today_rev = await session.scalar(
            text("""
                SELECT COALESCE(SUM(total_amount), 0) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND status != 'CANCELLED'
                AND created_at >= :since
            """),
            {"tid": tenant_id, "since": today_start}
        ) or 0

        yesterday_rev = await session.scalar(
            text("""
                SELECT COALESCE(SUM(total_amount), 0) FROM orders
                WHERE tenant_id = :tid AND deleted_at IS NULL
                AND status != 'CANCELLED'
                AND created_at BETWEEN :start AND :end
            """),
            {"tid": tenant_id, "start": yesterday_start, "end": yesterday_same_hour}
        ) or 0

        if yesterday_rev > 0 and today_rev < yesterday_rev * 0.3:
            return {
                "type": "revenue_drop",
                "severity": "WARNING",
                "message": f"📉 Doanh thu hôm nay ({today_rev:,.0f}đ) thấp hơn 70% so với cùng giờ hôm qua ({yesterday_rev:,.0f}đ).",
                "data": {"today": today_rev, "yesterday": yesterday_rev}
            }
        return None

    async def _persist_alerts(self, session: AsyncSession, alerts: List[Dict], tenant_id: str):
        """Create Notification records for detected anomalies (with dedup)."""
        for alert in alerts:
            # DEBT-4 fix: skip if same alert type already exists in last hour
            existing = await session.scalar(
                text("""
                    SELECT COUNT(*) FROM notifications
                    WHERE tenant_id = :tid AND message = :msg
                    AND created_at > NOW() - interval '1 hour'
                """),
                {"tid": tenant_id, "msg": alert["message"]}
            ) or 0

            if existing > 0:
                logger.debug(f"[AnomalyDetector] Skipping duplicate alert: {alert['type']}")
                continue

            await session.execute(
                text("""
                    INSERT INTO notifications (id, type, message, is_read, tenant_id, created_at, updated_at)
                    VALUES (:id, :type, :msg, false, :tid, NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "type": alert["severity"],
                    "msg": alert["message"],
                    "tid": tenant_id
                }
            )
        await session.commit()
