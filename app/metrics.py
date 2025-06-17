"""Prometheus metrics configuration."""
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
CALLBACK_COUNTER = Counter(
    'callback_total',
    'Total number of callbacks processed',
    ['status']  # success, error
)

CALLBACK_DURATION = Histogram(
    'callback_duration_seconds',
    'Time spent processing callbacks',
    ['target_url']
)

HMAC_ERRORS = Counter(
    'hmac_errors_total',
    'Total number of HMAC signing errors'
)

AMQP_RECONNECTS = Counter(
    'amqp_reconnects_total',
    'Total number of AMQP reconnection attempts'
)

def start_metrics_server(host: str, port: int) -> None:
    """Start Prometheus metrics HTTP server.
    
    Args:
        host (str): Host to bind the server to
        port (int): Port to bind the server to
    """
    start_http_server(port, addr=host)
