"""
Centralized logging configuration for the NCERT Voice Tutor.
Provides file + console logging with rotation.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    # File handler with rotation (5 MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d — %(message)s"
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
