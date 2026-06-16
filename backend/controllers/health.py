from __future__ import annotations

import json
import asyncio
import logging
from typing import AsyncGenerator
from datetime import datetime, timezone, timedelta

from litestar import Controller, get, post
from litestar.response import Stream
from litestar.exceptions import PermissionDeniedException, ValidationException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.health import (
    HealthStatusResponse,
    AnomalyResponse,
    SystemSnapshotResponse,
    DbHealthResponse,
    DbLocksResponse,
    DbBloatResponse,
    VacuumRequest,
    LiveHealthControlRequest,
    LiveHealthControlResponse,
)
from backend.services.health_service import health_service
from backend.services.db_health_service import db_health_service

logger = logging.getLogger("api-gateway.soc-health")


class HealthController(Controller):
    path = "/api/v1/health"

    @get("/")
    async def health_check(self) -> HealthStatusResponse:
        return HealthStatusResponse()

    @get("/detailed", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def get_system_anomalies(self, db_session: "AsyncSession") -> AnomalyResponse:
        """
        Fetch recent anomalies for XoHi Agent reporting.
        """
        return await health_service.get_system_anomalies(db_session)

    # ── SOC Telemetry & Telehealth (Module 1 & 5) ─────────────────────────────

    @get("/snapshot", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def get_system_snapshot(self) -> SystemSnapshotResponse:
        """
        Gathers system-wide telemetry: CPU, Process/VPS RAM, DB pool, Redis memory, EventBus, SSE counts.
        """
        return await health_service.get_system_snapshot()

    @get("/db", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def get_db_health(self) -> DbHealthResponse:
        """
        Get DB connection pool status, check-out leaks, and slow query stats.
        """
        return db_health_service.get_db_health()

    @get("/db/locks", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def get_db_locks(self, db_session: AsyncSession) -> DbLocksResponse:
        """
        Get active locks, running queries, and blocking transaction pairs from Postgres.
        """
        return await db_health_service.get_active_locks(db_session)

    @get("/db/bloat", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def get_db_bloat(self, db_session: AsyncSession) -> DbBloatResponse:
        """
        Rank user tables by fragmentation/dead tuples percentage.
        """
        return await db_health_service.get_table_bloat(db_session)

    @post("/db/vacuum", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def trigger_db_vacuum(self, db_session: AsyncSession, data: VacuumRequest) -> dict[str, str]:
        """
        Trigger autocommit VACUUM ANALYZE on a whitelisted table.
        """
        success = await db_health_service.trigger_vacuum(db_session, data.table)
        if not success:
            raise ValidationException("Table not in whitelist or vacuum execution failed.")
        return {"status": "success", "message": f"VACUUM ANALYZE triggered for table {data.table}"}

    # ── Live Health SSE Stream Control (Module 3) ─────────────────────────────

    @post("/live", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def control_live_health(self, data: LiveHealthControlRequest) -> LiveHealthControlResponse:
        """
        Enable or disable the on-demand SSE live stream.
        """
        if data.enable:
            health_service._live_enabled = True
            expires = datetime.now(timezone.utc) + timedelta(minutes=data.duration_minutes)
            health_service._live_expires_at = expires
            expires_str = expires.isoformat()
            logger.warning(f"[SOC Live Health] Enabled until {expires_str}")
        else:
            health_service._live_enabled = False
            health_service._live_expires_at = None
            expires_str = None
            logger.warning("[SOC Live Health] Disabled by administrator")

        return LiveHealthControlResponse(
            status="success",
            enabled=health_service._live_enabled,
            expires_at=expires_str,
        )

    @get("/live/stream", guards=[PermissionGuard(PermissionEnum.SYS_ADMIN)])
    async def stream_live_health(self) -> Stream:
        """
        Streams system health snapshot every 5s if active and not expired.
        """
        if not health_service._live_enabled:
            raise PermissionDeniedException("Live health stream is currently disabled. Enable it first via POST /health/live.")

        if health_service._live_expires_at and datetime.now(timezone.utc) > health_service._live_expires_at:
            health_service._live_enabled = False
            raise PermissionDeniedException("Live health stream has expired.")

        async def event_generator() -> AsyncGenerator[bytes, None]:
            try:
                yield b": live-health-success\n\n"
                while True:
                    # Check active and expiration status
                    if not health_service._live_enabled:
                        yield b"event: terminate\ndata: {\"message\": \"Live stream disabled by administrator.\"}\n\n"
                        break
                    
                    if health_service._live_expires_at and datetime.now(timezone.utc) > health_service._live_expires_at:
                        health_service._live_enabled = False
                        yield b"event: terminate\ndata: {\"message\": \"Live stream duration expired.\"}\n\n"
                        break

                    snapshot = await health_service.get_system_snapshot()
                    payload = snapshot.model_dump()
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                    
                    await asyncio.sleep(5.0)
            except (asyncio.CancelledError, GeneratorExit):
                pass
            except Exception as e:
                logger.error(f"[HealthController] Live stream exception: {e}")

        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
        return Stream(event_generator(), headers=headers)

