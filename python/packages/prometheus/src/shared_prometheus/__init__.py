"""Prometheus scrape setup for Starlette apps."""

from shared_prometheus.inbound_request_id import make_inbound_request_id_instrumentation
from shared_prometheus.prometheus_manager import PrometheusManager

__all__ = [
    "PrometheusManager",
    "make_inbound_request_id_instrumentation",
]
