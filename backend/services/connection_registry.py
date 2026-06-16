"""
Connection Registry (SOC Monitor V2.3)
=======================================
On-Demand SSE/WebSocket connection tracker.

Nguyên tắc: Mặc định OFF — không tốn RAM, không ghi nhận.
Admin bật qua POST /api/v1/security/connections/monitor {"enable": true}
Tự động tắt sau max_age_minutes nếu không có ai dùng.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("api-gateway.soc")


@dataclass
class ConnectionEntry:
    session_id: str
    conn_type: str          # "SSE_PULSE_CLIENT" | "SSE_PULSE_ADMIN" | "SSE_CONTENT"
    path: str
    ip: str
    user_agent: str
    connected_at: str       # ISO timestamp
    last_ping_at: str       # ISO timestamp — cập nhật mỗi heartbeat
    _kill_flag: bool = field(default=False, repr=False)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "conn_type": self.conn_type,
            "path": self.path,
            "ip": self.ip,
            "user_agent": self.user_agent[:100],
            "connected_at": self.connected_at,
            "last_ping_at": self.last_ping_at,
            "age_seconds": int(
                (datetime.now(timezone.utc) -
                 datetime.fromisoformat(self.connected_at)).total_seconds()
            ),
        }


class ConnectionRegistry:
    """
    Singleton registry theo dõi SSE/WS connections đang hoạt động.

    Mặc định INACTIVE — register() là no-op cho đến khi admin bật.
    Khi bật: ghi nhận connection vào dict in-memory (không Redis, không DB).
    Tự tắt sau `auto_disable_minutes` nếu không có ai query.
    """
    _instance: Optional["ConnectionRegistry"] = None

    def __new__(cls) -> "ConnectionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: Dict[str, ConnectionEntry] = {}
            cls._instance._enabled: bool = False
            cls._instance._enabled_at: Optional[str] = None
            cls._instance._last_queried_at: Optional[float] = None
            cls._instance._auto_disable_minutes: int = 60
            cls._instance._cleanup_task: Optional[asyncio.Task] = None
        return cls._instance

    # ── Control ───────────────────────────────────────────────────────────────

    def enable(self, auto_disable_minutes: int = 60) -> None:
        """Bật registry. Admin gọi qua API."""
        self._enabled = True
        self._auto_disable_minutes = auto_disable_minutes
        self._enabled_at = datetime.now(timezone.utc).isoformat()
        self._last_queried_at = _now()
        logger.warning(f"[SOC Registry] ENABLED (auto-disable in {auto_disable_minutes}m)")
        self._schedule_watchdog()

    def disable(self) -> None:
        """Tắt registry và xóa sạch dữ liệu để giải phóng RAM."""
        self._enabled = False
        self._connections.clear()
        self._enabled_at = None
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        logger.warning("[SOC Registry] DISABLED — all connection data cleared")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def status(self) -> dict:
        return {
            "enabled": self._enabled,
            "enabled_at": self._enabled_at,
            "active_connections": len(self._connections),
            "auto_disable_minutes": self._auto_disable_minutes,
        }

    # ── Lifecycle hooks (gọi từ stream handlers) ──────────────────────────────

    def register(
        self,
        session_id: str,
        conn_type: str,
        path: str,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> None:
        """No-op khi registry đang tắt — không tốn overhead."""
        if not self._enabled:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        self._connections[session_id] = ConnectionEntry(
            session_id=session_id,
            conn_type=conn_type,
            path=path,
            ip=ip,
            user_agent=user_agent,
            connected_at=now_iso,
            last_ping_at=now_iso,
        )
        logger.debug(f"[SOC Registry] +connection {session_id} ({conn_type})")

    def unregister(self, session_id: str) -> None:
        if session_id in self._connections:
            del self._connections[session_id]
            logger.debug(f"[SOC Registry] -connection {session_id}")

    def touch(self, session_id: str) -> None:
        """Cập nhật last_ping_at — gọi mỗi khi heartbeat được gửi."""
        if self._enabled and session_id in self._connections:
            self._connections[session_id].last_ping_at = datetime.now(timezone.utc).isoformat()

    # ── Kill Switch ────────────────────────────────────────────────────────────

    def kill(self, session_id: str) -> bool:
        """Đánh dấu kill flag. Generator loop phát hiện và tự ngắt."""
        if session_id in self._connections:
            self._connections[session_id]._kill_flag = True
            logger.warning(f"[SOC Registry] 🔴 KILL flagged: {session_id}")
            return True
        return False

    def kill_by_ip(self, ip: str) -> int:
        """Kill tất cả connections từ 1 IP. Trả về số connection bị kill."""
        count = 0
        for entry in self._connections.values():
            if entry.ip == ip:
                entry._kill_flag = True
                count += 1
        if count:
            logger.warning(f"[SOC Registry] 🔴 KILL-ALL for IP {ip}: {count} connection(s)")
        return count

    def is_killed(self, session_id: str) -> bool:
        """Generator loop gọi mỗi vòng để check kill flag."""
        entry = self._connections.get(session_id)
        return entry._kill_flag if entry else False

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_all(self) -> List[dict]:
        self._last_queried_at = _now()
        return [e.to_dict() for e in self._connections.values()]

    def get_count(self) -> int:
        return len(self._connections) if self._enabled else 0

    # ── Watchdog (tự tắt nếu không ai dùng) ──────────────────────────────────

    def _schedule_watchdog(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
            self._cleanup_task = loop.create_task(self._watchdog())
        except RuntimeError:
            pass  # Chưa có event loop — bỏ qua, watchdog sẽ được schedule khi enable() gọi lại

    async def _watchdog(self) -> None:
        """Tự tắt sau auto_disable_minutes nếu không có admin query nào."""
        try:
            while self._enabled:
                await asyncio.sleep(60)  # Check mỗi phút
                if self._last_queried_at is None:
                    continue
                idle_seconds = _now() - self._last_queried_at
                if idle_seconds > self._auto_disable_minutes * 60:
                    logger.warning(
                        f"[SOC Registry] Auto-disabled after {self._auto_disable_minutes}m idle"
                    )
                    self.disable()
                    break
        except asyncio.CancelledError:
            pass


def _now() -> float:
    import time
    return time.monotonic()


# Singleton toàn cục
connection_registry = ConnectionRegistry()
