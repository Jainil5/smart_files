import logging
import os
import sys
import yaml
from logging.handlers import RotatingFileHandler

from .config import LOGS_DIR, APP_RUNTIME_LOG

# --- Config ---
LOG_LEVEL = logging.INFO
# Added %(data_versions)s to the log format to track DVC/data versions
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | Data=[%(data_versions)s] | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_DIR = LOGS_DIR
# App-specific runtime logs
LOG_FILE = APP_RUNTIME_LOG

class DataVersionFilter(logging.Filter):
    """Injects data version tags into log records from a YAML file."""
    def __init__(self):
        super().__init__()
        self.version_str = "no-versions"
        try:
            # Assuming data_versions.yml is in the root directory
            yml_path = os.path.join(os.path.dirname(LOG_DIR), "data_versions.yml")
            if os.path.exists(yml_path):
                with open(yml_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data and "datasets" in data:
                        # e.g., sales:v1.0, health:v1.1
                        parts = [f"{k.split('_')[0]}:{v}" for k, v in data["datasets"].items()]
                        self.version_str = ",".join(parts)
        except Exception:
            pass

    def filter(self, record):
        record.data_versions = self.version_str
        return True


def _configure_root_logger():
    """Set up the root logger once with console + rotating file handlers."""
    root = logging.getLogger()
    if root.handlers:
        return  # Already configured

    root.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    version_filter = DataVersionFilter()

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(version_filter)
    root.addHandler(console)

    # Rotating file handler (5 MB max, keep 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(version_filter)
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
