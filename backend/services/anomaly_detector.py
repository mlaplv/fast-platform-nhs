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
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Union, TypedDict, Optional, Callable, Coroutine

# Phase 12: Rule R105 — CẤM dùng Any, dùng TypedDict cho cấu trúc tường minh.
class AnomalyAlert(TypedDict):
    type: str
    severity: str
    message: str
    data: Dict[str, object]

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

    def __init__(self) -> None:
        # Warm psutil CPU baseline ngay khi tạo object (non-blocking, ~0ms).
        # cpu_percent() lần đầu luôn trả 0.0 — phải gọi 1 lần trước để thiết lập
        # window đo đạc. Sau đó interval=None sẽ trả delta từ lần gọi trước — ZERO blocking.
        try:
            import psutil, os
            psutil.Process(os.getpid()).cpu_percent(interval=None)
        except Exception:
            pass

    async def scan(self, tenant_id: str = "default") -> List[AnomalyAlert]:
        """
        Run all anomaly checks in parallel (V76). Returns list of alerts.
        Each alert: {type, severity, message, data}
        """
        # Phase 76: Sequential Scalar Scanning for VPS 2GB Optimization
        # Rule: AsyncSession is NOT concurrency-safe on the same instance.
        # We call them one-by-one to avoid race conditions and "never awaited" warnings.
        alerts: List[AnomalyAlert] = []

        # Helper to run check safely
        # Note: Using object for *args to satisfy R105
        async def run_check(name: str, coro_func: Callable[..., Coroutine[None, None, Optional[AnomalyAlert]]], *args: object) -> None:
            try:
                # Coroutine[None, None, T] represents an async function returning T
                res = await coro_func(*args)
                if res:
                    alerts.append(res)
            except Exception as e:
                logger.warning(f"[AnomalyDetector] Check '{name}' failed: {e}")

        await run_check("cancelled_orders", self._check_cancelled_orders, tenant_id)
        await run_check("order_volume", self._check_order_volume, tenant_id)
        await run_check("revenue_anomaly", self._check_revenue_anomaly, tenant_id)
        await run_check("ai_latency", self._check_ai_latency, tenant_id)
        await run_check("db_pool", self._check_db_pool)
        await run_check("redis_replication", self._check_redis_replication)
        await run_check("docker_containers", self._check_docker_containers)
        # ── Performance & Resource Guards ────────────────────────────────────
        await run_check("memory_pressure", self._check_memory_pressure)   # RSS vs cgroup limit
        await run_check("swap_pressure", self._check_swap_pressure)        # Host swap saturation
        await run_check("cpu_pressure", self._check_cpu_pressure)          # CPU spike detection
        await run_check("disk_pressure", self._check_disk_pressure)        # Disk nearly full
        await run_check("event_loop_lag", self._check_event_loop_lag)      # asyncio stall detection
        await run_check("db_slow_queries", self._check_db_slow_queries)    # Accumulated slow queries
        await run_check("db_leak_rate", self._check_db_leak_rate)          # Connection leak counter

        if alerts:
            await self._persist_alerts(alerts, tenant_id)
            logger.info(f"[AnomalyDetector] {len(alerts)} anomalies detected and persisted.")
        else:
            logger.debug("[AnomalyDetector] Scan complete — no anomalies.")

        return alerts

    async def _check_ai_latency(self, tenant_id: str) -> Optional[AnomalyAlert]:
        """Check if recent AI response latencies are spiking using telemetry logs."""
        from backend.database.alchemy_config import alchemy_config
        maker = alchemy_config.create_session_maker()
        async with maker() as session:
            avg_latency = await session.scalar(
                text("""
                    SELECT AVG(duration_ms) 
                    FROM agent_telemetry_logs 
                    WHERE tenant_id = :tid 
                    AND created_at > NOW() - interval '30 minutes'
                """),
                {"tid": tenant_id}
            ) or 0

        if avg_latency > 5000: # Spike above 5s
            return AnomalyAlert(
                type="ai_latency_spike",
                severity="WARNING",
                message=f"⚡ Độ trễ AI đang tăng cao: Trung bình {avg_latency:.0f}ms trong 30p qua.",
                data={"avg_latency": avg_latency}
            )
        return None

    async def _check_memory_pressure(self) -> Optional[AnomalyAlert]:
        """
        [OOM Guard] Kiểm tra áp lực RAM của container API.
        Đọc /proc/meminfo của host và RSS của process hiện tại.
        - > 90% limit → CRITICAL (nguy cơ OOM kill ngay lập tức)
        - > 80% limit → WARNING (gần OOM)
        """
        import os
        try:
            import psutil
            process = psutil.Process(os.getpid())
            rss_bytes = process.memory_info().rss
            rss_mb = rss_bytes / (1024 * 1024)

            # Đọc container mem limit từ /sys/fs/cgroup (Docker cgroup v1/v2)
            limit_mb: float = 0
            for cgroup_path in [
                "/sys/fs/cgroup/memory/memory.limit_in_bytes",      # cgroup v1
                "/sys/fs/cgroup/memory.max",                        # cgroup v2
            ]:
                if os.path.exists(cgroup_path):
                    try:
                        with open(cgroup_path) as f:
                            raw = f.read().strip()
                        # "max" = unlimited trong cgroup v2
                        if raw not in ("max", ""):
                            limit_bytes = int(raw)
                            # Bỏ qua giá trị phi lý (> 1TB)
                            if limit_bytes < 1_099_511_627_776:
                                limit_mb = limit_bytes / (1024 * 1024)
                                break
                    except Exception:
                        pass

            # Fallback: dùng host total RAM nếu không đọc được cgroup
            if limit_mb <= 0:
                mem = psutil.virtual_memory()
                limit_mb = mem.total / (1024 * 1024)

            pct = (rss_mb / limit_mb * 100) if limit_mb > 0 else 0

            if pct >= 90:
                return AnomalyAlert(
                    type="memory_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [OOM ALERT] RAM API đạt {pct:.1f}% giới hạn "
                        f"({rss_mb:.0f}/{limit_mb:.0f} MiB). Nguy cơ OOM Kill ngay lập tức!"
                    ),
                    data={"rss_mb": round(rss_mb, 1), "limit_mb": round(limit_mb, 1), "pct": round(pct, 1)}
                )
            elif pct >= 80:
                return AnomalyAlert(
                    type="memory_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [Near-OOM] RAM API đạt {pct:.1f}% giới hạn "
                        f"({rss_mb:.0f}/{limit_mb:.0f} MiB). Hãy kiểm tra lưu lượng và tối ưu bộ nhớ."
                    ),
                    data={"rss_mb": round(rss_mb, 1), "limit_mb": round(limit_mb, 1), "pct": round(pct, 1)}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Memory pressure check failed: {e}")
        return None

    async def _check_swap_pressure(self) -> Optional[AnomalyAlert]:
        """
        [OOM Guard] Kiểm tra Swap usage của host.
        Swap > 50% = dấu hiệu hệ thống đang thiếu RAM thực, sắp ảnh hưởng hiệu năng.
        """
        try:
            import psutil
            swap = psutil.swap_memory()
            if swap.total <= 0:
                return None
            swap_pct = swap.percent
            swap_used_mb = swap.used / (1024 * 1024)
            swap_total_mb = swap.total / (1024 * 1024)

            if swap_pct >= 80:
                return AnomalyAlert(
                    type="swap_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [SWAP CRITICAL] Swap đạt {swap_pct:.1f}% "
                        f"({swap_used_mb:.0f}/{swap_total_mb:.0f} MiB). "
                        f"Hệ thống có nguy cơ OOM kill đột ngột!"
                    ),
                    data={"swap_pct": swap_pct, "swap_used_mb": round(swap_used_mb, 1), "swap_total_mb": round(swap_total_mb, 1)}
                )
            elif swap_pct >= 50:
                return AnomalyAlert(
                    type="swap_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [SWAP High] Host đang dùng {swap_pct:.1f}% Swap "
                        f"({swap_used_mb:.0f}/{swap_total_mb:.0f} MiB). "
                        f"RAM vật lý có thể đầy, hiệu năng sẽ giảm."
                    ),
                    data={"swap_pct": swap_pct, "swap_used_mb": round(swap_used_mb, 1), "swap_total_mb": round(swap_total_mb, 1)}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Swap pressure check failed: {e}")
        return None

    async def _check_db_pool(self) -> Optional[AnomalyAlert]:
        """Check SQLAlchemy connection pool utilization."""
        from backend.database.alchemy_config import alchemy_config
        engine = alchemy_config.get_engine()
        if hasattr(engine, "pool"):
            pool = engine.pool
            checkedin = pool.checkedin()
            checkedout = pool.checkedout()
            size = pool.size()
            
            # If checked out is near size
            if size > 0 and checkedout > size * 0.8:
                return AnomalyAlert(
                    type="db_pool_near_capacity",
                    severity="CRITICAL",
                    message=f"🔥 Database Connection Pool gần cạn: {checkedout}/{size} đang sử dụng.",
                    data={"checkedout": checkedout, "size": size}
                )
        return None

    async def _check_redis_replication(self) -> Optional[AnomalyAlert]:
        """Check Redis replication state (role must be master, no rogue replica setup)."""
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory._use_redis or not xohi_memory.client:
            return None
        
        try:
            info = await xohi_memory.client.info("replication")
            role = info.get("role", "master")
            if role != "master":
                master_host = info.get("master_host", "unknown")
                return AnomalyAlert(
                    type="redis_replica_hijack",
                    severity="CRITICAL",
                    message=f"🚨 CẢNH BÁO BẢO MẬT: Redis đã bị chuyển thành SLAVE của master lạ: {master_host}!",
                    data={"role": role, "master_host": master_host}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Redis replication check failed: {e}")
        return None

    async def _check_docker_containers(self) -> Optional[AnomalyAlert]:
        """Check if any core container has crashed or is in a crash loop."""
        import json
        import asyncio
        TARGET_CONTAINERS = [
            "fast_platform_worker_high",
            "fast_platform_api",
            "fast_platform_db",
            "fast_platform_redis",
        ]
        try:
            proc_ps = await asyncio.create_subprocess_exec(
                "docker", "ps", "-a", "--format", "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_ps, _ = await proc_ps.communicate()
            if proc_ps.returncode != 0:
                return None
            
            crashed = []
            for line in stdout_ps.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    name = data.get("Names")
                    if name in TARGET_CONTAINERS:
                        state = data.get("State", "").lower()
                        status = data.get("Status", "").lower()
                        if state != "running":
                            crashed.append(f"{name} ({state})")
                        elif "restarting" in status:
                            crashed.append(f"{name} (restarting)")
                except Exception:
                    continue
            
            if crashed:
                return AnomalyAlert(
                    type="container_crash",
                    severity="CRITICAL",
                    message=f"🚨 CẢNH BÁO HẠ TẦNG: Phát hiện container offline hoặc crash loop: {', '.join(crashed)}!",
                    data={"crashed_containers": crashed}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Docker container check failed: {e}")
        return None

    async def _check_cancelled_orders(self, tenant_id: str) -> Optional[AnomalyAlert]:
        """Compare cancelled orders last 1h vs 7-day hourly average."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        seven_days_ago = now - timedelta(days=7)

        from backend.database.alchemy_config import alchemy_config
        maker = alchemy_config.create_session_maker()
        async with maker() as session:
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
            return AnomalyAlert(
                type="cancelled_spike",
                severity="WARNING",
                message=f"⚠️ Đơn hủy tăng đột biến: {recent} đơn trong 1h qua (trung bình {baseline_hourly:.1f}/h).",
                data={"recent": recent, "baseline": round(float(baseline_hourly), 2)}
            )
        return None

    async def _check_order_volume(self, tenant_id: str) -> Optional[AnomalyAlert]:
        """Compare new order volume last 1h vs 7-day hourly average."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        seven_days_ago = now - timedelta(days=7)

        from backend.database.alchemy_config import alchemy_config
        maker = alchemy_config.create_session_maker()
        async with maker() as session:
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
            return AnomalyAlert(
                type="order_volume_spike",
                severity="INFO",
                message=f"📈 Đơn hàng mới bất thường: {recent} đơn trong 1h qua (trung bình {baseline_hourly:.1f}/h).",
                data={"recent": recent, "baseline": round(float(baseline_hourly), 2)}
            )
        return None

    async def _check_revenue_anomaly(self, tenant_id: str) -> Optional[AnomalyAlert]:
        """Compare today's revenue vs yesterday same hour."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_same_hour = yesterday_start + timedelta(hours=now.hour)

        from backend.database.alchemy_config import alchemy_config
        maker = alchemy_config.create_session_maker()
        async with maker() as session:
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
            return AnomalyAlert(
                type="revenue_drop",
                severity="WARNING",
                message=f"📉 Doanh thu hôm nay (đ{today_rev:,.0f}) thấp hơn 70% so với cùng giờ hôm qua (đ{yesterday_rev:,.0f}).",
                data={"today": float(today_rev), "yesterday": float(yesterday_rev)}
            )
        return None

    async def _persist_alerts(self, alerts: List[AnomalyAlert], tenant_id: str):
        """Create Notification records and dispatch to SignalCenter.
        SECURITY: All system anomaly alerts are stored with type prefix 'SYSTEM_'
        and user_id=NULL. They are ONLY visible to admin — NOT to end clients.
        """
        from backend.services.signal_center import signal_center
        from backend.schemas.signal import SignalSchema, SignalSeverity
        from backend.database.alchemy_config import alchemy_config

        severity_map = {
            "CRITICAL": SignalSeverity.CRITICAL,
            "WARNING": SignalSeverity.ACTION,
            "INFO": SignalSeverity.INFO,
        }

        maker = alchemy_config.create_session_maker()
        async with maker() as session:
            for alert in alerts:
                since = datetime.now(timezone.utc) - timedelta(hours=1)
                    
                existing = await session.scalar(
                    text("""
                        SELECT COUNT(*) FROM notifications
                        WHERE tenant_id = :tid AND message = :msg
                        AND created_at > :since
                    """),
                    {"tid": tenant_id, "msg": alert["message"], "since": since}
                ) or 0

                if existing > 0:
                    logger.debug(f"[AnomalyDetector] Skipping duplicate alert: {alert['type']}")
                    continue

                # SECURITY: Prefix type with SYSTEM_ so client-side query can exclude it.
                system_type = f"SYSTEM_{alert['severity']}"

                await signal_center.dispatch(
                    user_id="user_admin",
                    signal=SignalSchema(
                        message=alert["message"],
                        severity=severity_map.get(alert["severity"], SignalSeverity.ACTION),
                        signal_type=system_type,
                        payload=alert["data"],
                        persist=True
                    ),
                    tenant_id=tenant_id
                )

    # ══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE & RESOURCE CHECKS (V2.3)
    # ══════════════════════════════════════════════════════════════════════════

    async def _check_cpu_pressure(self) -> Optional[AnomalyAlert]:
        """
        Phát hiện CPU spike của process API.
        [OPT] Dùng interval=None (non-blocking, đọc delta từ lần gọi trước) thay vì
        interval=1.0 (block 1 giây). Baseline đã được warm trong __init__.
        Chi phí thực tế: < 1ms (chỉ đọc /proc/{pid}/stat).
        """
        try:
            import psutil, os
            process = psutil.Process(os.getpid())
            # interval=None: đọc CPU % từ lần gọi gần nhất trước đó — ZERO blocking
            cpu_pct: float = process.cpu_percent(interval=None)
            num_cpus = psutil.cpu_count(logical=True) or 1
            cpu_pct_normalized = cpu_pct / num_cpus

            if cpu_pct_normalized >= 85:
                return AnomalyAlert(
                    type="cpu_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [CPU CRITICAL] API process đang dùng {cpu_pct_normalized:.1f}% CPU "
                        f"(raw {cpu_pct:.1f}% / {num_cpus} cores). "
                        f"Nguy cơ throttling, response time sẽ tăng vọt."
                    ),
                    data={"cpu_pct": round(cpu_pct_normalized, 1), "raw_pct": round(cpu_pct, 1), "num_cpus": num_cpus}
                )
            elif cpu_pct_normalized >= 70:
                return AnomalyAlert(
                    type="cpu_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [CPU High] API process đang dùng {cpu_pct_normalized:.1f}% CPU "
                        f"({num_cpus} cores). Tải cao — kiểm tra background tasks."
                    ),
                    data={"cpu_pct": round(cpu_pct_normalized, 1), "raw_pct": round(cpu_pct, 1), "num_cpus": num_cpus}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] CPU pressure check failed: {e}")
        return None

    async def _check_disk_pressure(self) -> Optional[AnomalyAlert]:
        """
        Kiểm tra disk usage của partition chứa /app (code + logs + cache).
        > 95% → CRITICAL (sắp hết disk, log write sẽ fail → container crash)
        > 85% → WARNING  (cần dọn dẹp cache/log)
        """
        try:
            import psutil
            usage = psutil.disk_usage("/app")
            pct = usage.percent
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)

            if pct >= 95:
                return AnomalyAlert(
                    type="disk_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [DISK CRITICAL] Disk /app đầy {pct:.1f}% "
                        f"(chỉ còn {free_gb:.1f}/{total_gb:.1f} GB). "
                        f"Log write có thể fail — container sẽ crash!"
                    ),
                    data={"pct": pct, "free_gb": round(free_gb, 2), "total_gb": round(total_gb, 2)}
                )
            elif pct >= 85:
                return AnomalyAlert(
                    type="disk_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [Disk High] Disk /app đã dùng {pct:.1f}% "
                        f"(còn {free_gb:.1f} GB). Hãy dọn cache, log cũ, hoặc Docker images."
                    ),
                    data={"pct": pct, "free_gb": round(free_gb, 2), "total_gb": round(total_gb, 2)}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Disk pressure check failed: {e}")
        return None

    async def _check_event_loop_lag(self) -> Optional[AnomalyAlert]:
        """
        Đo asyncio event loop lag bằng cách tính drift của asyncio.sleep(0).
        Nếu sleep(0) thực tế mất > 200ms → event loop đang bị block bởi sync code.
        > 500ms → CRITICAL  (heavy blocking, toàn bộ API bị stall)
        > 200ms → WARNING   (stall nhẹ, có thể do import nặng hoặc GC pause)
        """
        try:
            import time
            start = time.perf_counter()
            await asyncio.sleep(0)  # Yield to event loop — nên trở về gần như tức thì
            lag_ms = (time.perf_counter() - start) * 1000

            if lag_ms >= 500:
                return AnomalyAlert(
                    type="event_loop_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [Event Loop BLOCKED] asyncio lag {lag_ms:.0f}ms! "
                        f"Có sync code đang block event loop — toàn bộ API bị stall."
                    ),
                    data={"lag_ms": round(lag_ms, 1)}
                )
            elif lag_ms >= 200:
                return AnomalyAlert(
                    type="event_loop_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [Event Loop Lag] asyncio lag {lag_ms:.0f}ms. "
                        f"Có thể do GC pause hoặc blocking I/O trong coroutine."
                    ),
                    data={"lag_ms": round(lag_ms, 1)}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] Event loop lag check failed: {e}")
        return None

    async def _check_db_slow_queries(self) -> Optional[AnomalyAlert]:
        """
        Đọc slow query counter từ _DB_STATS (zero I/O — in-memory only).
        Cảnh báo khi trong chu kỳ scan tích lũy > 5 slow queries (>1s mỗi query).
        Reset counter sau khi alert để tránh spam.
        """
        try:
            from backend.database.alchemy_config import _DB_STATS
            count = _DB_STATS.get("slow_query_count", 0)
            last_sql = _DB_STATS.get("last_slow_query_sql", "")
            last_dur = _DB_STATS.get("last_slow_query_duration_ms", 0)

            if count >= 10:
                # Reset để tránh alert spam liên tục
                _DB_STATS["slow_query_count"] = 0
                return AnomalyAlert(
                    type="db_slow_query_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [DB Slow Queries] {count} slow queries (>1s) tích lũy! "
                        f"Query chậm nhất: {last_dur}ms. Kiểm tra index và N+1 queries."
                    ),
                    data={"count": count, "last_sql": last_sql[:150], "last_dur_ms": last_dur}
                )
            elif count >= 5:
                _DB_STATS["slow_query_count"] = 0
                return AnomalyAlert(
                    type="db_slow_query_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [DB Slow Queries] {count} slow queries (>1s) trong chu kỳ scan. "
                        f"Query chậm nhất: {last_dur}ms. Xem xét tối ưu."
                    ),
                    data={"count": count, "last_sql": last_sql[:150], "last_dur_ms": last_dur}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] DB slow query check failed: {e}")
        return None

    async def _check_db_leak_rate(self) -> Optional[AnomalyAlert]:
        """
        Đọc connection leak counter từ _DB_STATS (in-memory, zero I/O).
        Cảnh báo khi có connection bị giữ >10s (checkout leak) trong chu kỳ scan.
        Reset counter sau khi alert.
        """
        try:
            from backend.database.alchemy_config import _DB_STATS
            count = _DB_STATS.get("leak_count", 0)
            last_dur = _DB_STATS.get("last_leak_duration_ms", 0)
            last_time = _DB_STATS.get("last_leak_time", "N/A")

            if count >= 3:
                _DB_STATS["leak_count"] = 0
                return AnomalyAlert(
                    type="db_connection_leak_critical",
                    severity="CRITICAL",
                    message=(
                        f"🚨 [DB Leak] {count} connection leaks (checkout >10s) phát hiện! "
                        f"Leak nghiêm trọng nhất: {last_dur}ms. "
                        f"Kiểm tra AI call trong transaction scope."
                    ),
                    data={"leak_count": count, "last_dur_ms": last_dur, "last_time": last_time}
                )
            elif count >= 1:
                _DB_STATS["leak_count"] = 0
                return AnomalyAlert(
                    type="db_connection_leak_warning",
                    severity="WARNING",
                    message=(
                        f"⚠️ [DB Leak] {count} connection leak (checkout >10s). "
                        f"Duration: {last_dur}ms lúc {last_time}."
                    ),
                    data={"leak_count": count, "last_dur_ms": last_dur, "last_time": last_time}
                )
        except Exception as e:
            logger.warning(f"[AnomalyDetector] DB leak rate check failed: {e}")
        return None
