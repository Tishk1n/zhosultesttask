"""Config module for the application."""
from dataclasses import dataclass
from typing import Final, Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass(frozen=True)
class Config:
    """Application configuration."""
    # AMQP
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    exchange: str = ""  # default exchange
    queue: str = "callbacks"
    routing_key: str = "callbacks"

    # HTTP
    default_method: str = "POST"
    retry_attempts: Final[int] = 3
    retry_delay: Final[int] = 1  # seconds

    # Metrics
    metrics_port: int = 8000
    metrics_host: str = "0.0.0.0"

    # Logger
    log_level: LogLevel = "INFO"


config: Final[Config] = Config()
