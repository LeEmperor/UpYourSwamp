import json
import threading
from pathlib import Path
from typing import Optional
from .schemas import BaseEvent, CommandDetected
from ..utils.logging import get_logger

logger = get_logger("event_sinks")

class EventSink:
    """Base class for event sinks."""

    def __init__(self, name: str):
        self.name = name

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an incoming event."""
        raise NotImplementedError

class StdoutLoggerSink(EventSink):
    """Sink that logs events to stdout."""

    def __init__(self):
        super().__init__("stdout_logger")

    def handle_event(self, event: BaseEvent) -> None:
        """Log event to stdout."""
        if isinstance(event, CommandDetected):
            print(f"🎤 COMMAND DETECTED: '{event.command_text}' (wake: '{event.wake_word}', confidence: {event.confidence})")
        else:
            print(f"📢 {event.event_type.upper()}: {event.model_dump_json()}")

class NDJSONFileSink(EventSink):
    """Sink that writes events to a newline-delimited JSON file."""

    def __init__(self, file_path: str = "events.log"):
        super().__init__("ndjson_file")
        self.file_path = Path(file_path)
        self._lock = threading.Lock()
        logger.info(f"NDJSON sink initialized, writing to: {self.file_path}")

    def handle_event(self, event: BaseEvent) -> None:
        """Write event as JSON line to file."""
        try:
            event_dict = event.model_dump()
            json_line = json.dumps(event_dict, ensure_ascii=False)

            with self._lock:
                with open(self.file_path, 'a', encoding='utf-8') as f:
                    f.write(json_line + '\n')

            logger.debug(f"Event written to {self.file_path}: {event.event_type}")

        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")

class DemoSubscriberSink(EventSink):
    """Demo subscriber that simulates video pipeline trigger."""

    def __init__(self):
        super().__init__("demo_subscriber")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle command detected events for demo."""
        if isinstance(event, CommandDetected):
            print(f"🎬 VIDEO_PIPELINE_TRIGGER: utterance_id={event.utterance_id} command='{event.command_text}'")
            logger.info(f"Demo subscriber triggered for command: {event.command_text}")

def create_default_sinks(log_file: str = "events.log") -> list[EventSink]:
    """Create the default set of event sinks.

    Args:
        log_file: Path to the NDJSON log file

    Returns:
        List of configured event sinks
    """
    return [
        StdoutLoggerSink(),
        NDJSONFileSink(log_file),
        DemoSubscriberSink()
    ]