from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from ..config.settings import settings


# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# Auth metrics
auth_login_total = Counter(
    "auth_login_total",
    "Total login attempts",
    ["status"],
)

auth_register_total = Counter(
    "auth_register_total",
    "Total registration attempts",
    ["status"],
)

auth_refresh_total = Counter(
    "auth_refresh_total",
    "Total token refresh attempts",
    ["status"],
)

# Execution metrics
executions_total = Counter(
    "executions_total",
    "Total executions",
    ["status"],
)

execution_duration_seconds = Histogram(
    "execution_duration_seconds",
    "Execution duration in seconds",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# WebSocket metrics
ws_connections_active = Gauge(
    "ws_connections_active",
    "Active WebSocket connections",
)

ws_messages_total = Counter(
    "ws_messages_total",
    "Total WebSocket messages",
    ["direction"],
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
)

# Rate limiting
rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit exceeded events",
    ["endpoint"],
)


def get_metrics() -> Response:
    """Generate Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics."""
    if not settings.METRICS_ENABLED:
        return
    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_auth_event(event: str, status: str):
    """Record authentication event metrics."""
    if not settings.METRICS_ENABLED:
        return
    if event == "login":
        auth_login_total.labels(status=status).inc()
    elif event == "register":
        auth_register_total.labels(status=status).inc()
    elif event == "refresh":
        auth_refresh_total.labels(status=status).inc()


def record_execution(status: str, duration: float = None):
    """Record execution metrics."""
    if not settings.METRICS_ENABLED:
        return
    executions_total.labels(status=status).inc()
    if duration:
        execution_duration_seconds.observe(duration)


def record_ws_event(direction: str):
    """Record WebSocket message metrics."""
    if not settings.METRICS_ENABLED:
        return
    ws_messages_total.labels(direction=direction).inc()


def set_ws_connections(count: int):
    """Set active WebSocket connections."""
    if not settings.METRICS_ENABLED:
        return
    ws_connections_active.set(count)


def record_db_query(query_type: str, duration: float):
    """Record database query metrics."""
    if not settings.METRICS_ENABLED:
        return
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_cache_event(hit: bool):
    """Record cache hit/miss."""
    if not settings.METRICS_ENABLED:
        return
    if hit:
        cache_hits_total.inc()
    else:
        cache_misses_total.inc()


def record_rate_limit_exceeded(endpoint: str):
    """Record rate limit exceeded."""
    if not settings.METRICS_ENABLED:
        return
    rate_limit_exceeded_total.labels(endpoint=endpoint).inc()