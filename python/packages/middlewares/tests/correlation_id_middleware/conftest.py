"""Shared fixtures for the correlation-id middleware tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from shared_log_manager import LogManager
from shared_middlewares import CorrelationIdMiddleware


def build_logging_app(log_manager: LogManager) -> Starlette:
    """Mount a single ``/ping`` handler behind ``CorrelationIdMiddleware``.

    Args:
        log_manager: Manager the handler logs through. Tests inspect its stream
            for the bound ``correlation_id``.

    Returns:
        An application whose only interesting behaviour is one log line per GET.
    """

    async def ping(_request: Request) -> JSONResponse:
        """Emit one record so tests can read the bound correlation id.

        Args:
            _request: Unused. The route contract requires it.

        Returns:
            A body the tests ignore; the log line is the assertion surface.
        """
        log_manager.get_child_logger("ping").info("ping.ok")
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/ping", ping)])
    app.add_middleware(CorrelationIdMiddleware)
    return app


@pytest.fixture
def app(log_manager: LogManager) -> Starlette:
    """Build the tiny logging app wrapped in ``CorrelationIdMiddleware``.

    Args:
        log_manager: Manager the ``/ping`` handler logs through.

    Returns:
        An application exposing ``GET /ping``.
    """
    return build_logging_app(log_manager)


@pytest.fixture
async def client(app: Starlette) -> AsyncGenerator[AsyncClient]:
    """Provide a client that speaks ASGI directly to the tiny app.

    Args:
        app: The application to send requests to.

    Yields:
        A client bound to that application.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://correlation.test",
    ) as http_client:
        yield http_client
