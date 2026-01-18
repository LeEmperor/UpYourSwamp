import threading
import queue
from typing import Dict, List, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
from .schemas import BaseEvent
from ..utils.logging import get_logger

logger = get_logger("event_bus")

class EventBus:
    """Simple in-process event bus with publish/subscribe pattern."""

    def __init__(self, max_workers: int = 4):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="event-bus")
        self._lock = threading.Lock()
        logger.info(f"EventBus initialized with {max_workers} worker threads")

    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], None]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event is published
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[BaseEvent], None]) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    logger.debug(f"Unsubscribed handler from event type: {event_type}")
                except ValueError:
                    logger.warning(f"Handler not found for event type: {event_type}")

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        event_type = event.event_type

        with self._lock:
            handlers = self._subscribers.get(event_type, []).copy()

        if not handlers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return

        logger.debug(f"Publishing {event_type} event to {len(handlers)} subscribers")

        # Submit each handler to the thread pool
        for handler in handlers:
            try:
                self._executor.submit(self._safe_handler_call, handler, event)
            except Exception as e:
                logger.error(f"Failed to submit handler for {event_type}: {e}")

    def _safe_handler_call(self, handler: Callable[[BaseEvent], None], event: BaseEvent) -> None:
        """Safely call a handler function with error handling."""
        try:
            handler(event)
        except Exception as e:
            logger.error(f"Handler failed for {event.event_type}: {e}", exc_info=True)

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type."""
        with self._lock:
            return len(self._subscribers.get(event_type, []))

    def shutdown(self, timeout: float = 5.0) -> None:
        """Shutdown the event bus and wait for pending tasks."""
        logger.info("Shutting down EventBus...")
        self._executor.shutdown(wait=True, timeout=timeout)
        logger.info("EventBus shutdown complete")

# Global event bus instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

def publish_event(event: BaseEvent) -> None:
    """Publish an event to the global event bus."""
    get_event_bus().publish(event)

def subscribe_to_event(event_type: str, handler: Callable[[BaseEvent], None]) -> None:
    """Subscribe to events on the global event bus."""
    get_event_bus().subscribe(event_type, handler)

def shutdown_event_bus() -> None:
    """Shutdown the global event bus."""
    global _event_bus
    if _event_bus:
        _event_bus.shutdown()
        _event_bus = None