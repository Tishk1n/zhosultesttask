"""Config module for the application."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration."""
    # AMQP
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    exchange: str = ""  # default exchange
    queue: str = "callbacks"
    routing_key: str = "callbacks"
    
    # HTTP
    default_method: str = "POST"
    retry_attempts: int = 3
    retry_delay: int = 1  # seconds
    
    # Metrics
    metrics_port: int = 8000
    metrics_host: str = "0.0.0.0"
    
    # Logger
    log_level: str = "INFO"

config = Config()
