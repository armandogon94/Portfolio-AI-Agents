"""Logging configuration.

See DECISIONS.md DEC-07 for rationale (JSON logs + /metrics, not Prometheus).
"""

import logging
import sys

from src.config.settings import settings


def setup_logging() -> logging.Logger:
    """Configure application logging.

    Production: JSON format (machine-parseable).
    Development: Human-readable format.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if settings.environment.value == "production":
            from pythonjsonlogger.json import JsonFormatter

            handler.setFormatter(
                JsonFormatter(
                    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
        else:
            fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

        root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    return root_logger
