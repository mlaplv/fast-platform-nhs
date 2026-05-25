import os
from datetime import datetime
import logging
from litestar import Controller, get, post, Request, Response
from litestar.exceptions import NotFoundException
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.services.ai_engine.core.security_guard import security_guard, ThreatAnalysis
from backend.services.security.draft_service import draft_service
from backend.schemas.common import SuccessResponse
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
                        entry = json.loads(line)
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

            return sorted(containers, key=lambda x: TARGET_CONTAINERS.index(x["name"]))
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
            
            # Thực thi lệnh Docker tương ứng
            proc = await asyncio.create_subprocess_exec(
                "docker", action, container_name,
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
            for actor in targets:
                # Update security stamp to invalidate all sessions
                new_stamp = str(uuid.uuid4())
                await db_session.execute(
                    update(User).where(User.email == actor).values(security_stamp=new_stamp)
                )
                processed_count += 1
            await db_session.commit()

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
