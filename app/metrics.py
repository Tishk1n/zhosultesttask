"""Prometheus metrics configuration."""
from typing import Final

from prometheus_client import Counter, Histogram, start_http_server

# Metrics
CALLBACK_COUNTER: Final[Counter] = Counter(
    'callback_total',
    'Total number of callbacks processed',
    ['status']  # success, error
)

CALLBACK_DURATION: Final[Histogram] = Histogram(
    'callback_duration_seconds',
    'Time spent processing callbacks',
    ['target_url'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf"))
)

HMAC_ERRORS: Final[Counter] = Counter(
    'hmac_errors_total',
    'Total number of HMAC signing errors'
)

AMQP_RECONNECTS: Final[Counter] = Counter(
    'amqp_reconnects_total',
    'Total number of AMQP reconnection attempts'
)


def start_metrics_server(host: str, port: int) -> None:
    """Start Prometheus metrics HTTP server.

    Args:
        host (str): Host to bind the server to
        port (int): Port to bind the server to
    """
    start_http_server(port=port, addr=host)
