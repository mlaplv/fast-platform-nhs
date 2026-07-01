"""
Agent Monitor Service — Phase 3
==============================
Tracks and gathers real-time telemetry metrics on AI Agent orders, errors, and token consumption.
"""
from __future__ import annotations
import logging
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("agent-monitor")

class AgentMonitor:
    @staticmethod
    async def record_order(is_sandbox: bool = False) -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            field = "sandbox" if is_sandbox else "real"
            await r.hincrby("agent:metrics:orders", field, 1)
        except Exception as e:
            logger.warning(f"Failed to record agent order metric: {e}")

    @staticmethod
    async def record_error(error_code: str) -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            await r.hincrby("agent:metrics:errors", error_code, 1)
            await r.incr("agent:metrics:total_errors")
        except Exception as e:
            logger.warning(f"Failed to record agent error metric: {e}")

    @staticmethod
    async def get_thresholds() -> list[float]:
        r = xohi_memory.client
        if not r:
            return [5.0, 10.0, 15.0, 20.0]
        try:
            import json
            data = await r.get("agent:metrics:thresholds")
            if data:
                loaded = json.loads(data)
                if isinstance(loaded, list) and len(loaded) == 4:
                    return [float(x) for x in loaded]
        except Exception:
            pass
        return [5.0, 10.0, 15.0, 20.0]

    @staticmethod
    async def set_thresholds(thresholds: list[float]) -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            import json
            await r.set("agent:metrics:thresholds", json.dumps(thresholds))
        except Exception as e:
            logger.warning(f"Failed to set thresholds in Redis: {e}")

    @staticmethod
    async def record_token_usage(input_tokens: int, output_tokens: int) -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            new_input = await r.hincrby("agent:metrics:tokens", "input", input_tokens)
            new_output = await r.hincrby("agent:metrics:tokens", "output", output_tokens)

            # Cumulative Cost Calculation in USD
            # Gemini-2.5-Flash prices: Input: $0.075 / M tokens | Output: $0.30 / M tokens
            cost_usd = ((new_input * 0.075) + (new_output * 0.30)) / 1_000_000

            # Record cost history (keep last 15 points)
            try:
                import datetime
                import json
                import time
                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                history_entry = {
                    "time": now_str,
                    "cost": float(cost_usd),
                    "input": int(new_input),
                    "output": int(new_output),
                    "timestamp": float(time.time())
                }
                await r.rpush("agent:metrics:history", json.dumps(history_entry))
                await r.ltrim("agent:metrics:history", -100, -1)
            except Exception as he:
                logger.warning(f"Failed to record agent budget history: {he}")

            # Alert and Shutdown limits
            thresholds = await AgentMonitor.get_thresholds()
            shutdown_threshold = thresholds[-1] if thresholds else 20.0
            critical_threshold = thresholds[-2] if len(thresholds) >= 2 else 15.0
            
            for limit in thresholds:
                if cost_usd >= limit:
                    alert_key = f"agent:metrics:alert_sent:{limit}"
                    if not await r.get(alert_key):
                        await r.set(alert_key, "1", ex=86400) # Cooldown lock for 24h

                        import asyncio
                        from backend.services.telegram_service import telegram_service
                        from backend.services.signal_center import signal_center
                        from backend.schemas.signal import SignalSchema, SignalSeverity

                        msg = (
                            f"🚨 <b>[A2A LLM BUDGET ALERT]</b>\n"
                            f"<b>Hạn mức tiêu thụ:</b> vượt quá <code>${limit:.2f}</code>\n"
                            f"<b>Tổng chi phí hiện tại:</b> <code>${cost_usd:.4f}</code>\n"
                            f"<b>Tokens Input:</b> <code>{new_input:,}</code>\n"
                            f"<b>Tokens Output:</b> <code>{new_output:,}</code>\n"
                        )

                        if limit >= shutdown_threshold:
                            msg += f"\n⚠️ <b>HÀNH ĐỘNG:</b> Tự động KHÓA & ĐÓNG HOÀN TOÀN cổng A2A Gateway để bảo vệ ngân sách!"
                            await r.set("agent:gateway:shutdown", "1")
                            logger.error(f"[A2A-Security] LLM Budget limit of ${shutdown_threshold} reached. Gateway SHUTDOWN activated.")
                        else:
                            msg += "\n<b>Trạng thái:</b> Đang giám sát chặt chẽ."

                        asyncio.create_task(telegram_service.send_alert(msg))

                        asyncio.create_task(signal_center.dispatch(
                            user_id="user_admin",
                            signal=SignalSchema(
                                message=f"Cảnh báo chi phí LLM A2A: Vượt quá ${limit:.2f} (Hiện tại: ${cost_usd:.4f})." +
                                        (f" Đóng hoàn toàn cổng A2A!" if limit >= shutdown_threshold else ""),
                                severity=SignalSeverity.CRITICAL if limit >= critical_threshold else SignalSeverity.ACTION,
                                signal_type="SYSTEM_SECURITY",
                                payload={
                                    "limit": limit,
                                    "current_cost": cost_usd,
                                    "input_tokens": new_input,
                                    "output_tokens": new_output,
                                    "shutdown": limit >= shutdown_threshold
                                },
                                persist=True
                            )
                        ))
        except Exception as e:
            logger.warning(f"Failed to record agent token metric: {e}")

    @staticmethod
    async def is_shutdown() -> bool:
        r = xohi_memory.client
        if not r:
            return False
        try:
            val = await r.get("agent:gateway:shutdown")
            return val == b"1" or val == "1"
        except Exception:
            return False

    @staticmethod
    async def reset_shutdown() -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            await r.delete("agent:gateway:shutdown")
            async for k in r.scan_iter(match="agent:metrics:alert_sent:*", count=50):
                await r.delete(k)
            await r.delete("agent:metrics:tokens")
            logger.info("[A2A-Security] A2A Gateway manually reopened and metrics reset.")
        except Exception as e:
            logger.warning(f"Failed to reset gateway shutdown status: {e}")

    @staticmethod
    async def record_ip(ip: str) -> None:
        r = xohi_memory.client
        if not r:
            return
        try:
            await r.sadd("agent:metrics:ips", ip)
        except Exception as e:
            logger.warning(f"Failed to record agent IP metric: {e}")

    @staticmethod
    async def get_stats() -> dict[str, int | bool | list[float] | list[dict[str, str | int | float]] | dict[str, int] | list[dict[str, str | int]]]:
        r = xohi_memory.client
        if not r:
            return {}
        try:
            orders = await r.hgetall("agent:metrics:orders")
            errors = await r.hgetall("agent:metrics:errors")
            tokens = await r.hgetall("agent:metrics:tokens")
            total_errors = await r.get("agent:metrics:total_errors")
            ips = await r.scard("agent:metrics:ips")
            
            # Check shutdown status
            is_sd = await r.get("agent:gateway:shutdown")
            is_sd_bool = (is_sd == b"1" or is_sd == "1")

            # Decode bytes if needed
            def decode_dict(d: dict[bytes | str, bytes | str | int | float]) -> dict[str, int]:
                return {k.decode() if isinstance(k, bytes) else str(k): int(v) for k, v in d.items()}
                
            # Scan for blacklist and infractions (SCAN — non-blocking, O(1) per batch)
            blacklisted_ips: list[dict[str, str | int]] = []
            infraction_ips: list[dict[str, str | int]] = []
            
            # 1. Blacklist
            async for k in r.scan_iter(match="support:blacklist:*", count=50):
                k_str = k.decode() if isinstance(k, bytes) else str(k)
                ip = k_str.replace("support:blacklist:", "")
                ttl = await r.ttl(k_str)
                blacklisted_ips.append({
                    "ip": ip,
                    "ttl": ttl
                })
                
            # 2. Infractions
            async for k in r.scan_iter(match="support:security_infractions:*", count=50):
                k_str = k.decode() if isinstance(k, bytes) else str(k)
                ip = k_str.replace("support:security_infractions:", "")
                val = await r.get(k_str)
                ttl = await r.ttl(k_str)
                infraction_ips.append({
                    "ip": ip,
                    "count": int(val) if val else 0,
                    "ttl": ttl
                })
                
            thresholds = await AgentMonitor.get_thresholds()
            
            # Fetch only the last 15 items for the inline status check
            history_data = await r.lrange("agent:metrics:history", -15, -1)
            history: list[dict[str, str | int | float]] = []
            if history_data:
                import json
                for h in history_data:
                    try:
                        h_str = h.decode() if isinstance(h, bytes) else str(h)
                        history.append(json.loads(h_str))
                    except Exception:
                        pass

            return {
                "orders": decode_dict(orders or {}),
                "errors": decode_dict(errors or {}),
                "tokens": decode_dict(tokens or {}),
                "total_errors": int(total_errors) if total_errors else 0,
                "unique_ips": int(ips) if ips else 0,
                "blacklisted_ips": blacklisted_ips,
                "infraction_ips": infraction_ips,
                "is_shutdown": is_sd_bool,
                "thresholds": thresholds,
                "history": history
            }
        except Exception as e:
            logger.warning(f"Failed to get agent metrics: {e}")
            return {}

    @staticmethod
    async def get_history_page(cursor: Optional[float] = None, limit: int = 15) -> list[dict[str, str | int | float]]:
        r = xohi_memory.client
        if not r:
            return []
        try:
            history_data = await r.lrange("agent:metrics:history", 0, -1)
            if not history_data:
                return []
                
            history: list[dict[str, str | int | float]] = []
            import json
            for h in history_data:
                try:
                    h_str = h.decode() if isinstance(h, bytes) else str(h)
                    history.append(json.loads(h_str))
                except Exception:
                    pass
            history.reverse()

            if cursor is None:
                return history[:limit]

            cursor_idx = -1
            for idx, item in enumerate(history):
                if item.get("timestamp") == cursor:
                    cursor_idx = idx
                    break

            if cursor_idx == -1:
                # If cursor timestamp is not found (might have expired/pruned), return first page
                return history[:limit]

            return history[cursor_idx + 1 : cursor_idx + 1 + limit]
        except Exception as e:
            logger.warning(f"Failed to get agent history page: {e}")
            return []
