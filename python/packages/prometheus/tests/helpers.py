"""Tiny Starlette app mirroring a composition root's PrometheusManager wiring."""

from prometheus_client import CollectorRegistry
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from shared_config import PrometheusConfig
from shared_prometheus import PrometheusManager, make_inbound_request_id_instrumentation


def instrumented_app(
    registry: CollectorRegistry,
    config: PrometheusConfig | None = None,
) -> Starlette:
    """App with ``GET /ping`` and ``GET /metrics`` on a private collector.

    Mirrors a composition root's Prometheus wiring: construct ``PrometheusManager``,
    then ``add_http_instrumentation``, then ``add_middleware``, then
    ``add_metrics_router``.

    Args:
        registry: Private collector so this test cannot collide with another.
        config: Gzip for the scrape path. Defaults to ``PrometheusConfig()``.

    Returns:
        An application with ``GET /ping`` and ``GET /metrics``.
    """

    async def ping(_request: Request) -> JSONResponse:
        """Return a body the tests ignore.

        Args:
            _request: Unused. The route contract requires it.

        Returns:
            A trivial JSON payload.
        """
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/ping", ping)])
    prometheus = PrometheusManager(registry=registry)
    prometheus.add_http_instrumentation(
        make_inbound_request_id_instrumentation(prometheus.registry),
    )
    prometheus.add_middleware(app)
    prometheus.add_metrics_router(
        app,
        config if config is not None else PrometheusConfig(),
    )
    return app
