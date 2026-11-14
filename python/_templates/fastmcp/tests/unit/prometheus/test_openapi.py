"""``GET /metrics`` is served but omitted from schema."""

from http import HTTPStatus

from httpx import ASGITransport, AsyncClient
from prometheus_client import CollectorRegistry
from starlette.routing import Route

from shared_config import METRICS_ENDPOINT
from tests.unit.prometheus.helpers import instrumented_app


async def test_metrics_is_omitted_from_schema_and_still_served() -> None:
    """Prometheus text is a scrape contract, not a product route."""
    app = instrumented_app(CollectorRegistry())
    include_in_schema_by_path = {
        route.path: route.include_in_schema
        for route in app.routes
        if isinstance(route, Route) and route.path in {METRICS_ENDPOINT, "/ping"}
    }

    assert include_in_schema_by_path[METRICS_ENDPOINT] is False
    assert include_in_schema_by_path["/ping"] is True

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://metrics.test",
    ) as client:
        response = await client.get(METRICS_ENDPOINT)

    assert response.status_code == HTTPStatus.OK
