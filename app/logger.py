"""Logger configuration module."""
import logging
import sys
from pythonjsonlogger import jsonlogger

from app.config import config

def setup_logger() -> logging.Logger:
    """Set up and configure JSON logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("callback_service")
    logger.setLevel(config.log_level)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()
