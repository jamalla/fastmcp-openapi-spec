"""
Logging configuration for Salla MCP Server.
Provides structured logging with JSON and text formats.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)

        return json.dumps(log_obj)


class TextFormatter(logging.Formatter):
    """Text log formatter for human-readable output."""

    _format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(self):
        """Initialize formatter."""
        super().__init__(self._format, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(name: str, level: str = "INFO", format_type: str = "text") -> logging.Logger:
    """
    Setup logging with specified configuration.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format (json, text)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Set formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance by name."""
    return logging.getLogger(name)
