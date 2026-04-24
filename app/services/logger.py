import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from .config import LOGS_DIR, APP_RUNTIME_LOG

# --- Config ---
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_DIR = LOGS_DIR
# App-specific runtime logs
LOG_FILE = APP_RUNTIME_LOG


def _configure_root_logger():
    """Set up the root logger once with console + rotating file handlers."""
    root = logging.getLogger()
    if root.handlers:
        return  # Already configured

    root.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler (5 MB max, keep 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


_configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger. Use __name__ as the name so log lines
    show the exact module they came from.

    Example:
        logger = get_logger(__name__)
        logger.info("Starting ingestion pipeline")
    """
    return logging.getLogger(name)
