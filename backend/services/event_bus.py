import asyncio
import logging
import time
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
    R23: Zero-latency internal event bus for Proactive Nerve System (V56.5).
    Uses a non-blocking queue for asynchronous event processing.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InternalBus, cls).__new__(cls)
            cls._instance.subscribers: Dict[str, List[Callable]] = {}
            cls._instance.broadcast_subscribers: List[asyncio.Queue] = []
            cls._instance.queue = asyncio.Queue()
            cls._instance._worker_task = None
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        logger.debug(f"[EventBus] Subscribed to {event_name}")

    def unsubscribe(self, event_name: str, callback: Callable):
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
        event = SystemEvent(name=event_name, payload=payload)
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.error(f"[EventBus] GLOBAL QUEUE FULL! Dropping event {event_name}")

    async def start(self):
        """Start the background worker to process events."""
        if self._worker_task is None:
            # Set global queue limit for VPS safety
            self.queue = asyncio.Queue(maxsize=1000)
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("[EventBus] Background worker started with safety limits.")

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except (asyncio.CancelledError, Exception):
                pass
            self._worker_task = None
            logger.info("[EventBus] Background worker stopped.")

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
