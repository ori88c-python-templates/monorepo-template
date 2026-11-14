"""HTTP-layer series that counts inbound ``X-Request-ID``."""

from collections.abc import Callable
from typing import Final, Protocol

from prometheus_client import CollectorRegistry, Counter

from shared_middlewares import REQUEST_ID_HEADER

_INBOUND_REQUEST_ID_METRIC: Final = "http_requests_with_inbound_request_id_total"


class _HeaderMap(Protocol):
    def get(self, key: str, default: str = "") -> str | None:
        """Return a header value, or ``default`` when the name is absent."""


class _HttpRequest(Protocol):
    headers: _HeaderMap


class _InstrumentationInfo(Protocol):
    request: _HttpRequest


def make_inbound_request_id_instrumentation(
    registry: CollectorRegistry,
) -> Callable[..., object]:
    """Count requests that arrived with ``X-Request-ID`` already set.

    This reads the Starlette request, so it lives with Prometheus rather than
    with a product metric. The series shows where an HTTP callback belongs.
    It is not a product concern.

    Args:
        registry: The same registry ``PrometheusManager`` exposes at ``/metrics``.

    Returns:
        An instrumentation callback for ``PrometheusManager.add_http_instrumentation``.
    """
    counter: Final = Counter(
        _INBOUND_REQUEST_ID_METRIC,
        "Requests that arrived with an X-Request-ID header.",
        registry=registry,
    )

    def record_inbound_request_id(info: _InstrumentationInfo) -> None:
        """Increment when the caller supplied a request id.

        Args:
            info: Request context from prometheus-fastapi-instrumentator.
        """
        inbound = info.request.headers.get(REQUEST_ID_HEADER, "") or ""
        if inbound.strip():
            counter.inc()

    return record_inbound_request_id
