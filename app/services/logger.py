"""
Centralized logging configuration for Smart Files project.

Usage in any module:
    from services.logger import get_logger
    logger = get_logger(__name__)

    logger.info("File uploaded successfully")
    logger.warning("Duplicate file detected")
    logger.error("Failed to connect to DB")
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# --- Config ---
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file path: project_root/logs/smart_files.log
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(_BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "smart_files.log")
os.makedirs(LOG_DIR, exist_ok=True)


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
