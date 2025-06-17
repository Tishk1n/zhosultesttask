"""Logger configuration module."""
import logging
import sys
from typing import Final

from pythonjsonlogger import jsonlogger

from app.config import config

LOG_FORMAT: Final[str] = "%(asctime)s %(name)s %(levelname)s %(message)s"
LOGGER_NAME: Final[str] = "callback_service"


def setup_logger() -> logging.Logger:
    """Set up and configure JSON logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(config.log_level)

    # Remove existing handlers if any
    logger.handlers.clear()

    # Add new handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger: Final[logging.Logger] = setup_logger()
