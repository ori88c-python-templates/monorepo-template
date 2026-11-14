"""HTTP middleware used by both FastAPI and FastMCP apps."""

from shared_middlewares.constants import (
    CORRELATION_ID_HEADER,
    CORRELATION_ID_STATE_KEY,
    REQUEST_ID_HEADER,
)
from shared_middlewares.correlation_id_middleware import CorrelationIdMiddleware
from shared_middlewares.unhandled_http_exception_handler import (
    make_unhandled_http_exception_handler,
)

__all__ = [
    "CORRELATION_ID_HEADER",
    "CORRELATION_ID_STATE_KEY",
    "REQUEST_ID_HEADER",
    "CorrelationIdMiddleware",
    "make_unhandled_http_exception_handler",
]
