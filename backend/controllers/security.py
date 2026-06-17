import os
from datetime import datetime
import logging
from litestar import Controller, delete, get, post, Request, Response
from litestar.exceptions import NotFoundException, ValidationException, PermissionDeniedException
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.services.ai_engine.core.security_guard import security_guard, ThreatAnalysis
from backend.services.security.draft_service import draft_service
from backend.schemas.common import SuccessResponse
from backend.schemas.health import (
    MonitorControlRequest,
    MonitorStatusResponse,
    ConnectionListResponse,
    ConnectionRegistryItem,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

import json
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger(__name__)

class SecurityController(Controller):
    path = "/api/v1/security"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]
    tags = ["Security"]

    async def _read_audit_logs(self, limit: int = 100, suspicious_only: bool = False) -> List[Dict]:
        """Internal logic to read logs without Litestar route overhead."""
        log_path = "logs/audit.log"
        if not os.path.exists(log_path):
            return []

        logs = []
        try:
            # Fallback to stable read for current file size
            with open(log_path, "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    try:
                        line_str = line.strip()
                        if not line_str:
                            continue
                        if "{" in line_str:
                            line_str = line_str[line_str.index("{"):]
                        entry = json.loads(line_str)
                        if not suspicious_only or entry.get("suspicious"):
                            logs.append(entry)
                            if len(logs) >= limit:
                                break
                    except: continue
        except Exception as e:
            logger.error(f"❌ [Security] Critical log access error: {e}")
            return []

        # Elite V2.2: Auto-Seed if empty to avoid blank UI
        if not logs:
            logs.append({
                "timestamp": datetime.now().isoformat(),
                "action": "SYSTEM_SOC_ONLINE",
                "actor": "SYSTEM",
                "ip": "127.0.0.1",
                "suspicious": False,
                "ms": 0
            })
        return logs


    @get("/audit-logs")
    async def get_audit_logs(self, limit: int = 100, suspicious_only: bool = False) -> Response:
        """
        [ELITE V2.2] Lấy danh sách log Forensic mới nhất (Optimized for 2GB RAM).
        """
        logs = await self._read_audit_logs(limit=limit, suspicious_only=suspicious_only)
        return Response(
            content=logs,
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
        )

    @post("/audit-logs/clear")
    async def clear_audit_logs(self) -> SuccessResponse:
        """
        [ELITE V2.2] Xóa sạch nhật ký audit trail log file.
        """
        log_path = "logs/audit.log"
        try:
            with open(log_path, "w") as f:
                f.write("")
            return SuccessResponse(message="Đã làm sạch nhật ký an ninh thành công.")
        except Exception as e:
            logger.error(f"❌ [Security] Clear logs failure: {e}")
            return SuccessResponse(message=f"Lỗi làm sạch log: {e}")

    @post("/analyze-threat")
    async def analyze_threat(self, data: Dict) -> ThreatAnalysis:
        """
        Gửi một dòng log cho Security Agent phân tích chuyên sâu.
        """
        log_entry = json.dumps(data)
        return await security_guard.analyze_log_entry(log_entry)

    @get("/containers")
    async def get_containers(self) -> List[Dict]:
        """
        [ELITE V2.2] Lấy trạng thái tài nguyên thực tế của các container core (SOC).
        """
        import asyncio
        import json
        
        TARGET_CONTAINERS = [
            "fast_platform_worker_fraud",
            "fast_platform_worker_default",
            "fast_platform_worker_high",
            "fast_platform_api",
            "fast_platform_db",
            "fast_platform_redis",
            "fast_platform_caddy"
        ]

        try:
            # 1. Chạy docker ps
            proc_ps = await asyncio.create_subprocess_exec(
                "docker", "ps", "-a", "--format", "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_ps, _ = await proc_ps.communicate()
            
            # 2. Chạy docker stats
            proc_stats = await asyncio.create_subprocess_exec(
                "docker", "stats", "--no-stream", "--format", "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_stats, _ = await proc_stats.communicate()

            # Parse stats
            stats_dict = {}
            for line in stdout_stats.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    name = data.get("Name")
                    if name:
                        stats_dict[name] = data
                except:
                    continue

            # Parse ps
            containers = []
            ps_names = set()
            for line in stdout_ps.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    name = data.get("Names")
                    if name in TARGET_CONTAINERS:
                        ps_names.add(name)
                        stat = stats_dict.get(name, {})
                        containers.append({
                            "name": name,
                            "id": data.get("ID"),
                            "state": data.get("State"), # running, exited, etc.
                            "status": data.get("Status"), # Up 2 hours
                            "image": data.get("Image"),
                            "cpu": stat.get("CPUPerc", "0.00%"),
                            "mem_usage": stat.get("MemUsage", "0B / 0B"),
                            "mem_perc": stat.get("MemPerc", "0.00%"),
                            "pids": stat.get("PIDs", "0")
                        })
                except:
                    continue

            # Thêm các container không tìm thấy trong ps (coi như offline/chưa tạo)
            for name in TARGET_CONTAINERS:
                if name not in ps_names:
                    containers.append({
                        "name": name,
                        "id": "N/A",
                        "state": "offline",
                        "status": "Not Created",
                        "image": "N/A",
                        "cpu": "0.00%",
                        "mem_usage": "0B / 0B",
                        "mem_perc": "0.00%",
                        "pids": "0"
                    })

            return containers
        except Exception as e:
            logger.error(f"❌ [Security SOC] Failed to fetch container stats: {e}")
            return []

    @post("/containers/action")
    async def container_action(self, data: Dict) -> SuccessResponse:
        """
        [ELITE V2.2] Thực hiện thao tác chuyên nghiệp trên Container (SOC Operations).
        """
        import asyncio
        container_name = data.get("container_name")
        action = data.get("action") # start, stop, restart

        TARGET_CONTAINERS = [
            "fast_platform_worker_fraud",
            "fast_platform_worker_default",
            "fast_platform_worker_high",
            "fast_platform_api",
            "fast_platform_db",
            "fast_platform_redis",
            "fast_platform_caddy"
        ]

        if container_name not in TARGET_CONTAINERS:
            raise NotFoundException(detail="Container không thuộc quyền quản lý của SOC.")

        if action not in ["start", "stop", "restart"]:
            raise NotFoundException(detail="Thao tác không được hỗ trợ.")

        try:
            logger.warning(f"🚨 [SOC OPS] Admin triggered container action: {action} on {container_name}")
            
            # Bản đồ ánh xạ từ container_name sang service_name tương ứng trong docker-compose
            SERVICE_MAP = {
                "fast_platform_worker_fraud": "worker_fraud",
                "fast_platform_worker_default": "worker_default",
                "fast_platform_worker_high": "worker_high",
                "fast_platform_api": "api",
                "fast_platform_db": "db",
                "fast_platform_redis": "redis",
                "fast_platform_caddy": "caddy"
            }

            service_name = SERVICE_MAP.get(container_name)
            if service_name:
                if action == "start":
                    # Dùng '--profile admin' để tự động tạo mới & chạy container kể cả khi đã bị prune dọn dẹp
                    cmd = ["docker", "compose", "--profile", "admin", "up", "-d", service_name]
                elif action == "stop":
                    cmd = ["docker", "compose", "--profile", "admin", "stop", service_name]
                else: # restart
                    cmd = ["docker", "compose", "--profile", "admin", "restart", service_name]
            else:
                # Fallback về docker CLI truyền thống
                cmd = ["docker", action, container_name]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8").strip()
                logger.error(f"❌ [SOC OPS] Failed to {action} container {container_name}: {err_msg}")
                return SuccessResponse(message=f"Lỗi: {err_msg}")

            return SuccessResponse(message=f"Thành công: Đã {action} container {container_name}")
        except Exception as e:
            logger.error(f"❌ [SOC OPS] Critical exception during container action: {e}")
            return SuccessResponse(message=f"Lỗi hệ thống: {str(e)}")

    @get("/status")
    async def get_security_status(self) -> Dict:
        """
        [ELITE V2.2] Thống kê nhanh tình hình an ninh cho Dashboard.
        """
        # Elite V2.2: Mandatory Late-Initialization Guard
        if not trinity_bridge._initialized or trinity_bridge.rotator.get_count() == 0:
            try:
                await trinity_bridge.initialize()
            except Exception as e:
                logger.warning(f"⚠️ [SecurityController] AI Engine initialization delayed: {e}")

        logs = await self._read_audit_logs(limit=100)
        suspicious_count = sum(1 for l in logs if l.get("suspicious"))
        
        # Lấy nhịp tim từ AI Engine
        ai_heartbeat = "ACTIVE" if trinity_bridge._initialized else "INITIALIZING"
        
        # Nếu chưa có log thực tế, thêm một log hệ thống để Sếp không thấy trống trải
        active_keys = trinity_bridge.rotator.get_count()
        logger.info(f"📊 [SOC] Status requested. Keys: {active_keys} | Logs: {len(logs)}")

        # Elite V2.2: Sync Status via Redis
        is_read_only = os.getenv("SYSTEM_READ_ONLY", "false").lower() == "true"
        if trinity_bridge.rotator._use_redis and trinity_bridge.rotator.client:
            redis_status = await trinity_bridge.rotator.client.get("security:martial_law")
            if redis_status:
                is_read_only = redis_status == "1"

        return Response(
            content={
                "is_read_only": is_read_only,
                "ai_status": ai_heartbeat,
                "threat_level": "LOW" if suspicious_count < 2 else ("MEDIUM" if suspicious_count < 5 else "HIGH"),
                "active_keys": active_keys,
                "suspicious_events": suspicious_count,
                "total_logs": len(logs)
            },
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
        )

    @post("/martial-law")
    async def toggle_martial_law(self, data: Dict) -> SuccessResponse:
        """
        [THIẾT QUÂN LUẬT] Bật/Tắt chế độ chỉ đọc toàn hệ thống (Synced via Redis).
        """
        enabled = data.get("enabled", False)
        
        from backend.services.ai_engine.core.key_rotator import key_rotator
        if key_rotator._use_redis and key_rotator.client:
            await key_rotator.client.set("security:martial_law", "1" if enabled else "0")
            
        # Fallback for process-local legacy checks
        os.environ["SYSTEM_READ_ONLY"] = "true" if enabled else "false"
        
        logger.warning(f"🚨 [SECURITY] Martial Law status changed to: {enabled}")
        return SuccessResponse(message=f"Martial Law {'activated' if enabled else 'deactivated'}")

    @post("/bulk-action")
    async def security_bulk_action(self, data: Dict, db_session: AsyncSession) -> SuccessResponse:
        """
        [THIẾT QUÂN LUẬT] Thực hiện thao tác an ninh hàng loạt.
        """
        action = data.get("action")
        targets = data.get("targets", []) # List of IPs or UserEmails
        
        from backend.services.ai_engine.core.key_rotator import key_rotator
        from sqlalchemy import update, select
        from backend.database.models import User
        import uuid

        processed_count = 0
        if action == "BLACKLIST":
            if key_rotator._use_redis and key_rotator.client:
                for ip in targets:
                    await key_rotator.client.set(f"security:blacklist:ip:{ip}", "1", ex=86400 * 30) # Block 30 days
                    processed_count += 1
        
        elif action == "REVOKE":
            user_ids_to_invalidate = []
            for actor in targets:
                # Update security stamp to invalidate all sessions
                new_stamp = str(uuid.uuid4())
                result = await db_session.execute(
                    update(User).where(User.email == actor).values(security_stamp=new_stamp).returning(User.id)
                )
                revoked_id = result.scalar_one_or_none()
                if revoked_id:
                    user_ids_to_invalidate.append(str(revoked_id))
                processed_count += 1
            await db_session.commit()
            # Invalidate Redis stamp cache — kick ngay, không chờ TTL 5 phút
            if key_rotator._use_redis and key_rotator.client and user_ids_to_invalidate:
                keys = [f"security:stamp:{uid}" for uid in user_ids_to_invalidate]
                await key_rotator.client.delete(*keys)

        return SuccessResponse(message=f"Thành công: Đã thực hiện {action} trên {processed_count} mục tiêu.")

    @get("/drafts")
    async def list_drafts(self, db_session: AsyncSession) -> List[Dict]:
        """
        [THIẾT QUÂN LUẬT] Liệt kê các thao tác đang chờ phê duyệt.
        """
        drafts = await draft_service.list_drafts(db_session)
        return [
            {
                "id": str(d.id),
                "requested_by_email": d.proposed_by,
                "action_type": f"{d.action} {d.target_model}",
                "description": f"Yêu cầu {d.action} trên {d.target_model} id={d.target_id}",
                "payload": d.payload,
                "created_at": d.created_at.isoformat()
            } for d in drafts
        ]

    @post("/drafts/{draft_id:str}/approve")
    async def approve_action(self, request: Request, db_session: AsyncSession, draft_id: str) -> SuccessResponse:
        """
        [THIẾT QUÂN LUẬT] Phê duyệt và thực thi thao tác.
        """
        reviewer_id = request.state.user.get("sub", "ADMIN")
        return await draft_service.approve_draft(db_session, draft_id, reviewer_id)

    @post("/drafts/{draft_id:str}/reject")
    async def reject_action(self, request: Request, db_session: AsyncSession, draft_id: str) -> SuccessResponse:
        """
        [THIẾT QUÂN LUẬT] Từ chối thao tác.
        """
        reviewer_id = request.state.user.get("sub", "ADMIN")
        return await draft_service.reject_draft(db_session, draft_id, reviewer_id)

    @get("/whitelist/phones")
    async def get_whitelist_phones(self) -> List[str]:
        """[ELITE V2.2] Lấy danh sách số điện thoại Whitelist từ Redis."""
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return []
        phones = await xohi_memory.client.smembers("spam:whitelist:phones")
        return [p.decode("utf-8") if isinstance(p, bytes) else str(p) for p in phones]

    @post("/whitelist/phones")
    async def add_whitelist_phone(self, data: Dict) -> SuccessResponse:
        """[ELITE V2.2] Thêm số điện thoại vào Whitelist trong Redis."""
        phone = data.get("phone", "").strip()
        if not phone:
            raise NotFoundException(detail="Số điện thoại không hợp lệ.")
        
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return SuccessResponse(message="Lỗi kết nối Redis.", success=False)
            
        await xohi_memory.client.sadd("spam:whitelist:phones", phone)
        # Clear any existing rate limiting history for this phone to reset score to 0
        await xohi_memory.client.delete(
            f"spam:last:phone:{phone}",
            f"spam:sync:phone:{phone}",
            f"spam:v2026:phone:{phone}"
        )
        return SuccessResponse(message=f"Đã thêm số {phone} vào danh sách trắng thành công.")

    @delete("/whitelist/phones/{phone:str}", status_code=200)
    async def remove_whitelist_phone(self, phone: str) -> SuccessResponse:
        """[ELITE V2.2] Xóa số điện thoại khỏi Whitelist trong Redis."""
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return SuccessResponse(message="Lỗi kết nối Redis.", success=False)
            
        await xohi_memory.client.srem("spam:whitelist:phones", phone)
        return SuccessResponse(message=f"Đã xóa số {phone} khỏi danh sách trắng thành công.")

    # ── Connection Registry & Monitor Control (Module 2 & 3) ─────────────────

    @post("/connections/monitor")
    async def control_connections_monitor(self, data: MonitorControlRequest) -> MonitorStatusResponse:
        """
        Enable/Disable the live Connection Registry to track active connections.
        """
        from backend.services.connection_registry import connection_registry
        if data.enable:
            connection_registry.enable(auto_disable_minutes=data.auto_disable_minutes)
        else:
            connection_registry.disable()
        
        status = connection_registry.status()
        return MonitorStatusResponse(
            enabled=status["enabled"],
            enabled_at=status["enabled_at"],
            active_connections=status["active_connections"],
            auto_disable_minutes=status["auto_disable_minutes"],
        )

    @get("/connections")
    async def get_active_connections(self) -> ConnectionListResponse:
        """
        Get all active connections tracked in the registry.
        """
        from backend.services.connection_registry import connection_registry
        conns = connection_registry.get_all()
        items = []
        for c in conns:
            items.append(
                ConnectionRegistryItem(
                    session_id=c["session_id"],
                    conn_type=c["conn_type"],
                    path=c["path"],
                    ip=c["ip"],
                    user_agent=c["user_agent"],
                    connected_at=c["connected_at"],
                    last_ping_at=c["last_ping_at"],
                    age_seconds=c["age_seconds"],
                )
            )
        return ConnectionListResponse(
            status="success",
            count=len(items),
            connections=items,
        )

    @delete("/connections/{session_id:str}", status_code=200)
    async def kill_connection(self, session_id: str) -> SuccessResponse:
        """
        Force kill an active connection by setting its kill flag.
        """
        from backend.services.connection_registry import connection_registry
        killed = connection_registry.kill(session_id)
        if not killed:
            return SuccessResponse(message="Không tìm thấy kết nối hoặc không thể đóng.", success=False)
        return SuccessResponse(message="Đã ra lệnh ngắt kết nối cưỡng bức thành công.", success=True)

    @post("/connections/kill-all")
    async def kill_all_connections(self, data: dict[str, str]) -> SuccessResponse:
        """
        Force kill all connections from a specific IP.
        """
        ip = data.get("ip", "").strip()
        if not ip:
            raise ValidationException("Missing ip parameter")
        
        from backend.services.connection_registry import connection_registry
        count = connection_registry.kill_by_ip(ip)
        return SuccessResponse(message=f"Đã gửi lệnh ngắt {count} kết nối từ IP {ip} thành công.", success=True)

    # ── Redis Ops Panel (Module 4) ──────────────────────────────────────────

    @get("/redis/info")
    async def get_redis_info(self) -> dict[str, object]:
        """
        Get Redis server information (memory usage, connected clients, peak memory, max memory).
        """
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return {"status": "offline", "message": "Redis is not active."}
        
        try:
            info = await xohi_memory.client.info("memory")
            clients = await xohi_memory.client.info("clients")
            return {
                "status": "success",
                "used_memory_mb": round(float(info.get("used_memory", 0)) / (1024 * 1024), 2),
                "maxmemory_mb": round(float(info.get("maxmemory", 0)) / (1024 * 1024), 2),
                "used_memory_peak_mb": round(float(info.get("used_memory_peak", 0)) / (1024 * 1024), 2),
                "maxmemory_policy": info.get("maxmemory_policy", "volatile-lru"),
                "connected_clients": int(clients.get("connected_clients", 0)),
                "uptime_seconds": int(info.get("uptime_in_seconds", 0)) if "uptime_in_seconds" in info else 0
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @get("/redis/keys")
    async def get_redis_keys(self, pattern: str = "*") -> List[str]:
        """
        Scan keys in Redis safely using SCAN (never KEYS) to protect performance on production.
        """
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return []
        
        keys = []
        cursor = 0
        try:
            while len(keys) < 1000:
                cursor, batch = await xohi_memory.client.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"[Security Redis] Scan failed: {e}")
            return []
        return keys

    @delete("/redis/key/{key:str}", status_code=200)
    async def delete_redis_key(self, key: str) -> SuccessResponse:
        """
        Delete a specific key from Redis.
        """
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return SuccessResponse(message="Redis offline", success=False)
        
        try:
            deleted = await xohi_memory.client.delete(key)
            if deleted:
                return SuccessResponse(message=f"Đã xóa key '{key}' thành công.", success=True)
            return SuccessResponse(message=f"Không tìm thấy key '{key}' để xóa.", success=False)
        except Exception as e:
            return SuccessResponse(message=f"Lỗi: {e}", success=False)

    @post("/redis/flush-namespace")
    async def flush_redis_namespace(self, data: dict[str, str]) -> SuccessResponse:
        """
        Flush all keys matching a specific whitelisted prefix namespace.
        """
        prefix = data.get("prefix", "").strip()
        if not prefix:
            raise ValidationException("Missing prefix parameter")
        
        WHITELIST_PREFIXES = {"pulse:", "tts:req:", "security:blacklist:", "spam:", "helen:"}
        if prefix not in WHITELIST_PREFIXES:
            raise ValidationException(f"Prefix not in whitelist. Allowed prefixes: {', '.join(WHITELIST_PREFIXES)}")
        
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory.client:
            return SuccessResponse(message="Redis offline", success=False)
        
        try:
            cursor = 0
            count = 0
            while True:
                cursor, keys = await xohi_memory.client.scan(cursor, match=f"{prefix}*", count=100)
                if keys:
                    await xohi_memory.client.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
            return SuccessResponse(message=f"Đã xóa sạch {count} keys với prefix {prefix} thành công.", success=True)
        except Exception as e:
            return SuccessResponse(message=f"Lỗi: {e}", success=False)

