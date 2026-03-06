import asyncio
import logging
from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger("api-gateway")

@dataclass
class SystemEvent:
    name: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=asyncio.get_event_loop().time)

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
            cls._instance.queue = asyncio.Queue()
            cls._instance._worker_task = None
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        logger.debug(f"[EventBus] Subscribed to {event_name}")

    async def emit(self, event_name: str, payload: Dict[str, Any]):
        """Emit event to queue for background processing (Non-blocking for Request)"""
        event = SystemEvent(name=event_name, payload=payload)
        await self.queue.put(event)

    async def start(self):
        """Start the background worker to process events."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("[EventBus] Background worker started.")

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
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
            except Exception as e:
                logger.error(f"[EventBus] Error processing {event.name}: {e}")
            finally:
                self.queue.task_done()

# Global instance
event_bus = InternalBus()
