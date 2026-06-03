import asyncio
import os
import logging
import time
import json
from typing import Callable, Union, Dict, List, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

logger = logging.getLogger("api-gateway")

@dataclass
class SystemEvent:
    name: str
    payload: Dict[str, object]
    timestamp: float = field(default_factory=time.time)

class InternalBus:
    """
    R82: Internal Event Bus — High-performance Pub/Sub for system synchronization.
    
    [SECURITY WARNING]
    ================
    Events emitted via .emit() ARE BROADCAST to the Pulse SSE stream and potentially
    exposed to the Admin UI. NEVER emit raw PII (Phone, Address, Full Name) in the 
    payload unless you intend for it to be visible in the broadcast layer.
    Use mask_pii() at the consumer level (PulseStreamController) or emit lean IDs only.
    """
    _instance = None

    def __new__(cls) -> "InternalBus":
        if cls._instance is None:
            cls._instance = super(InternalBus, cls).__new__(cls)
            cls._instance.subscribers: Dict[str, List[Callable]] = {}
            cls._instance.broadcast_subscribers: List[asyncio.Queue] = []
            cls._instance.queue: Optional[asyncio.Queue] = None
            cls._instance._worker_task: Union[asyncio.Task, None] = None
            cls._instance._redis_task: Union[asyncio.Task, None] = None
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable) -> None:
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        logger.debug(f"[EventBus] Subscribed to {event_name}")

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        if event_name in self.subscribers and callback in self.subscribers[event_name]:
            self.subscribers[event_name].remove(callback)
            logger.debug(f"[EventBus] Unsubscribed from {event_name}")

    @asynccontextmanager
    async def subscribe_context(self, event_name: str) -> AsyncGenerator[asyncio.Queue, None]:
        """
        Context manager to subscribe to an event and yield updates into a queue.
        Useful for SSE streaming.
        """
        # Limit queue size to 100 to prevent memory blowup if client is slow (V76)
        queue = asyncio.Queue(maxsize=100)

        async def callback(payload: object):
            try:
                # Use nowait to avoid blocking the bus if one subscriber is slow
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning(f"[EventBus] Queue full for {event_name}, dropping event.")

        self.subscribe(event_name, callback)
        try:
            yield queue
        finally:
            self.unsubscribe(event_name, callback)

    def subscribe_broadcast(self, queue: asyncio.Queue):
        self.broadcast_subscribers.append(queue)
        logger.debug(f"[EventBus] Added broadcast subscriber (Total: {len(self.broadcast_subscribers)})")

    def unsubscribe_broadcast(self, queue: asyncio.Queue):
        if queue in self.broadcast_subscribers:
            self.broadcast_subscribers.remove(queue)
            logger.debug(f"[EventBus] Removed broadcast subscriber")

    async def emit(self, event_name: str, payload: Dict[str, object]):
        """Emit event to queue for background processing (Non-blocking for Request)"""
        if event_name == "CONTENT_PROGRESS":
            msg = payload.get("message", "")
            if any(k in str(msg) for k in ["[BRAIN]", "[ROLE]", "[RECON]", "✅", "❌"]):
                logger.warning(f"📡 [BUS] Emitting: {msg}")
        if self.queue is None:
            self.queue = asyncio.Queue(maxsize=1000)
            
        event = SystemEvent(name=event_name, payload=payload)
        
        # Elite V2.2: Cross-Container Redis PubSub Bridge & Stateful Pulse Caching
        # IMPORTANT: Two INDEPENDENT if blocks so SUPPORT_INBOX_UPDATE always reaches BOTH client AND admin
        if event_name in ["SUPPORT_RESPONSE_READY", "SUPPORT_INBOX_UPDATE", "OTP_UPDATE"] and "session_id" in payload:
            async def _bg_bridge_session(p_load: dict, e_name: str):
                try:
                    from backend.services.xohi_memory import xohi_memory
                    import json
                    if xohi_memory._use_redis and xohi_memory.client:
                        str_payload = json.dumps(p_load, ensure_ascii=False)
                        await asyncio.wait_for(
                            xohi_memory.client.publish(f"pulse:{p_load['session_id']}", str_payload),
                            timeout=2.0
                        )
                        if e_name in ["SUPPORT_RESPONSE_READY", "OTP_UPDATE"]:
                            cache_key = f"pulse:{p_load['session_id']}:cache"
                            await xohi_memory.client.set(cache_key, str_payload, ex=300)
                except Exception as e:
                    logger.error(f"❌ [EventBus] Session bridge failed: {e}")

            asyncio.create_task(_bg_bridge_session(payload, event_name))

        # ─── INDEPENDENT block: always publish to admin:pulse regardless of above ───
        # CRITICAL FIX: was `elif` before — meaning admin never got SUPPORT_INBOX_UPDATE
        # when a session_id was present (which is always the case for chat events).
        # V91: _origin='local' tag → _redis_listener will NOT re-queue these locally
        #      (prevents double subscriber processing + double SSE broadcast)
        if event_name in ["CONTENT_PROGRESS", "AGENT_TASK_COMPLETED", "MEDIA_ANALYZED", "SYSTEM_SIGNAL", "SUPPORT_INBOX_UPDATE"]:
            async def _bg_bridge_admin(p_load: dict, e_name: str):
                try:
                    from backend.services.xohi_memory import xohi_memory
                    import json
                    if xohi_memory._use_redis and xohi_memory.client:
                        str_payload = json.dumps({"event": e_name, "payload": p_load, "_origin": "local"}, ensure_ascii=False)
                        await asyncio.wait_for(
                            xohi_memory.client.publish("admin:pulse", str_payload),
                            timeout=2.0
                        )
                except Exception as e:
                    # CNS V90.5: Log to warning so it shows in Sếp's filtered terminal
                    logger.warning(f"⚠️ [EventBus] Admin bridge failed: {e}")

            asyncio.create_task(_bg_bridge_admin(payload, event_name))

        # Local distribution
        try:
            if self.queue is None: self.queue = asyncio.Queue(maxsize=1000)
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.error(f"❌ [EventBus] GLOBAL QUEUE FULL! Dropping event {event_name}")

    async def stream_emit(self, stream_name: str, payload: Dict[str, object]):
        """
        [Elite V3.0] Durable Event Streaming via Redis Streams (Slow Path).
        Allows consumer groups and background forensic processing.
        """
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory._use_redis or not xohi_memory.client:
            logger.warning(f"⚠️ [EventBus] Redis not available for stream: {stream_name}")
            return

        try:
            # Flatten payload for Redis Stream (Redis Streams store field-value pairs)
            # We wrap the whole payload as a JSON string under a 'data' key for complexity
            safe_payload = {"data": json.dumps(payload, ensure_ascii=False)}
            await xohi_memory.client.xadd(f"stream:{stream_name}", safe_payload, maxlen=10000, approximate=True)
            logger.info(f"📡 [StreamBus] Event added to {stream_name}")
        except Exception as e:
            logger.error(f"❌ [StreamBus] Failed to emit to stream {stream_name}: {e}")


    async def start(self):
        """Start the background worker to process events."""
        if self._worker_task is None:
            # Set global queue limit for VPS safety
            if self.queue is None:
                self.queue = asyncio.Queue(maxsize=1000)
            self._worker_task = asyncio.create_task(self._worker())
            
            # [Elite V2.2] Skip Redis listener in test environment to avoid hangs
            if os.getenv("FAST_PLATFORM_TEST") != "true":
                self._redis_task = asyncio.create_task(self._redis_listener())
                logger.info("[EventBus] Background worker and Redis listener started.")
            else:
                logger.info("[EventBus] Background worker started (Redis listener skipped for test).")

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            if hasattr(self, "_redis_task") and self._redis_task:
                self._redis_task.cancel()
            try:
                if hasattr(self, "_redis_task") and self._redis_task:
                    await asyncio.gather(self._worker_task, self._redis_task, return_exceptions=True)
                else:
                    await self._worker_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[EventBus] Error during stop: {e}")
            self._worker_task = None
            if hasattr(self, "_redis_task"):
                self._redis_task = None
            logger.info("[EventBus] Background workers stopped.")

    async def _redis_listener(self) -> None:
        from backend.services.xohi_memory import xohi_memory
        import json
        
        # Give xohi_memory a bit of time to initialize
        await asyncio.sleep(2)
        
        # Explicit type check for client
        if not xohi_memory._use_redis or getattr(xohi_memory, "client", None) is None:
            return
            
        try:
            pubsub = xohi_memory.client.pubsub()
            await pubsub.subscribe("admin:pulse")
            logger.info("[EventBus] Subscribed to Redis admin:pulse cross-container bridge.")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message and message.get('type') == 'message':
                    try:
                        data: Dict[str, object] = json.loads(message['data'])
                        event_name: str = str(data.get("event", ""))
                        origin: str = str(data.get("_origin", ""))

                        # V91: Skip events that originated from THIS container (already in local queue)
                        # Only process events from OTHER containers (arq workers, etc.)
                        if origin == "local":
                            logger.debug(f"[EventBus] Skipping local-origin Redis event: {event_name}")
                            continue

                        # Elite V2.2: Safe payload extraction without type: ignore
                        raw_payload = data.get("payload")
                        if event_name and isinstance(raw_payload, dict):
                            payload: Dict[str, object] = raw_payload
                            local_event = SystemEvent(name=event_name, payload=payload)
                            try:
                                self.queue.put_nowait(local_event)
                            except asyncio.QueueFull:
                                logger.warning(f"[EventBus] Local Queue Full, dropped Redis event: {event_name}")
                    except Exception as parse_e:
                        logger.error(f"[EventBus] Failed to parse Redis message: {parse_e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[EventBus] Redis listener error: {e}")

    async def _worker(self):
        while True:
            event = await self.queue.get()
            try:
                callbacks = self.subscribers.get(event.name, [])
                if callbacks:
                    # Execute all callbacks for this event
                    await asyncio.gather(*(cb(event.payload) for cb in callbacks), return_exceptions=True)

                # Rule R82.31: Agent Pulse Broadcast (SSE Native)
                # Forward everything to pulse listeners
                if self.broadcast_subscribers:
                    for sub_queue in self.broadcast_subscribers:
                        try:
                            sub_queue.put_nowait(event)
                        except asyncio.QueueFull:
                            pass # Skip slow broadcast listeners
            except Exception as e:
                logger.error(f"[EventBus] Error processing {event.name}: {e}")
            finally:
                self.queue.task_done()

# Global instance
event_bus = InternalBus()
