import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", format_str: str = None) -> logging.Logger:
    """Setup logging configuration for the voice command demo.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_str: Custom format string, uses default if None

    Returns:
        Configured logger instance
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger("voice_cmd_demo")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    formatter = logging.Formatter(format_str)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str = "voice_cmd_demo") -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name (will be prefixed with voice_cmd_demo)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"voice_cmd_demo.{name}")