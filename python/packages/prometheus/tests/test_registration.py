"""HTTP instrumentation callbacks must be registered before middleware is installed."""

import pytest
from prometheus_client import CollectorRegistry
from starlette.applications import Starlette

from shared_config import METRICS_ENDPOINT, PrometheusConfig
from shared_prometheus import PrometheusManager


def test_http_instrumentation_cannot_be_added_after_middleware() -> None:
    """Callbacks after ``add_middleware`` never reach the already-installed ASGI wrapper."""
    manager = PrometheusManager(registry=CollectorRegistry())
    manager.add_middleware(Starlette())

    def unused_callback(*_args: object, **_kwargs: object) -> None:
        """No-op callback used only to exercise the registration guard."""

    with pytest.raises(RuntimeError, match="before add_middleware"):
        manager.add_http_instrumentation(unused_callback)


def test_middleware_cannot_be_installed_twice() -> None:
    """One manager wraps one app."""
    manager = PrometheusManager(registry=CollectorRegistry())
    manager.add_middleware(Starlette())
    with pytest.raises(RuntimeError, match="already installed"):
        manager.add_middleware(Starlette())


def test_metrics_router_uses_the_shared_path() -> None:
    """Mounting scrape does not require a FastAPI subclass."""
    manager = PrometheusManager(registry=CollectorRegistry())
    app = Starlette()
    manager.add_metrics_router(app, PrometheusConfig())
    mounted = {getattr(route, "path", None) for route in app.routes}
    assert METRICS_ENDPOINT in mounted
