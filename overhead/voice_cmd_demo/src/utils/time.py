import time
from datetime import datetime, timezone
from typing import Optional

def get_iso_timestamp() -> str:
    """Get current timestamp in ISO format with timezone.

    Returns:
        ISO 8601 formatted timestamp string
    """
    return datetime.now(timezone.utc).isoformat()

def get_unix_timestamp() -> float:
    """Get current Unix timestamp.

    Returns:
        Unix timestamp as float
    """
    return time.time()

def format_duration_ms(duration_s: float) -> int:
    """Convert duration in seconds to milliseconds.

    Args:
        duration_s: Duration in seconds

    Returns:
        Duration in milliseconds as integer
    """
    return int(duration_s * 1000)

def sleep_ms(duration_ms: int) -> None:
    """Sleep for specified milliseconds.

    Args:
        duration_ms: Duration to sleep in milliseconds
    """
    time.sleep(duration_ms / 1000.0)