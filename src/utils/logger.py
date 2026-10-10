"""Logging setup.

All modules log through the ``sis`` logger namespace (``sis.service``,
``sis.storage`` ...). Logs go to a rotating file so they never grow forever.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src.utils.config import Config

LOGGER_NAME = "sis"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s"


def setup_logging(config: Config) -> logging.Logger:
    """Configure and return the application's root logger."""
    log_file = config.path("logging.file")
    log_file.parent.mkdir(parents=True, exist_ok=True)  # the sample crashed if logs/ was missing

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(str(config.get("logging.level", "INFO")).upper())
    logger.handlers.clear()  # avoid duplicate lines if called twice
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(config.get("logging.max_bytes", 1_048_576)),
        backupCount=int(config.get("logging.backup_count", 3)),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console logging is off by default so log lines don't clutter the menu.
    if config.get("logging.console", False):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
