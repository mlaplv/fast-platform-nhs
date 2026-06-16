import logging
from datetime import datetime, timedelta, timezone
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.health import AnomalyResponse, AnomalyItem, SystemSnapshotResponse

logger = logging.getLogger("api-gateway")

class HealthService:
    _live_enabled: bool = False
    _live_expires_at: Optional[datetime] = None

    @staticmethod
    async def get_system_anomalies(db_session: AsyncSession) -> AnomalyResponse:
        """
        Fetch recent anomalies for XoHi Agent reporting. R1.5: Zero-Hydration.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Scalar query to fetch recent alerts
        stmt = text("""
            SELECT id, type, message, created_at
            FROM notifications
            WHERE type IN ('WARNING', 'CRITICAL')
            AND created_at > :since
            ORDER BY created_at DESC
            LIMIT 5
        """)
        result = await db_session.execute(stmt, {"since": since})
        rows = result.all()
        anomalies = [
            AnomalyItem(id=str(r[0]), type=r[1], message=r[2], time=r[3].isoformat())
            for r in rows
        ]

        return AnomalyResponse(
            status="success",
            count=len(anomalies),
            anomalies=anomalies
        )

    @staticmethod
    async def get_system_snapshot() -> SystemSnapshotResponse:
        """
        Gathers system-wide telemetry: CPU, Process/VPS RAM, DB pool, Redis memory, EventBus, SSE counts.
        """
        from backend.services.xohi_memory import xohi_memory
        from backend.services.event_bus import event_bus
        from backend.services.connection_registry import connection_registry
        from backend.services.db_health_service import db_health_service

        # 1. Process CPU and RAM
        process = psutil.Process()
        ram_process_rss_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=None)

        # 2. VPS RAM
        vps_mem = psutil.virtual_memory()
        ram_vps_total_mb = vps_mem.total / (1024 * 1024)
        ram_vps_used_mb = vps_mem.used / (1024 * 1024)
        ram_vps_used_percent = vps_mem.percent

        # 3. DB Pool Checked out connections
        db_pool_checkedout = db_health_service.get_pool_status().checkedout

        # 4. Redis Memory Usage
        redis_used_mb = 0.0
        redis_max_mb = 0.0
        redis_peak_mb = 0.0

        if xohi_memory._use_redis and xohi_memory.client:
            try:
                info = await xohi_memory.client.info("memory")
                redis_used_mb = float(info.get("used_memory", 0)) / (1024 * 1024)
                redis_max_mb = float(info.get("maxmemory", 0)) / (1024 * 1024)
                redis_peak_mb = float(info.get("used_memory_peak", 0)) / (1024 * 1024)
            except Exception as e:
                logger.error(f"[HealthService] Redis memory info query failed: {e}")

        # 5. Broadcast Subscribers
        event_bus_subs = len(event_bus.broadcast_subscribers)

        # 6. SSE connections count
        sse_conn_count = connection_registry.get_count()

        return SystemSnapshotResponse(
            status="success",
            ram_process_rss_mb=round(ram_process_rss_mb, 2),
            ram_vps_total_mb=round(ram_vps_total_mb, 2),
            ram_vps_used_mb=round(ram_vps_used_mb, 2),
            ram_vps_used_percent=round(ram_vps_used_percent, 2),
            cpu_percent=round(cpu_percent, 2),
            db_pool_checkedout=db_pool_checkedout,
            redis_used_memory_mb=round(redis_used_mb, 2),
            redis_maxmemory_mb=round(redis_max_mb, 2),
            redis_peak_memory_mb=round(redis_peak_mb, 2),
            event_bus_subscribers=event_bus_subs,
            sse_connections_count=sse_conn_count,
        )

health_service = HealthService()

