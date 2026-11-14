"""Shared fixtures for the unhandled HTTP exception handler tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from shared_log_manager import LogManager
from shared_middlewares import CorrelationIdMiddleware, make_unhandled_http_exception_handler


def build_unhandled_exception_app(log_manager: LogManager) -> Starlette:
    """App with ``GET /boom``, ``GET /missing``, and ``GET /ok``.

    Mirrors production: the ``Exception`` handler is registered, then correlation
    id is the outer middleware.

    Args:
        log_manager: Manager whose ``uvicorn`` child the handler logs through.

    Returns:
        An application whose unhandled errors become a generic 500.
    """

    async def boom(_request: Request) -> Response:
        """Raise an unhandled error so the generic 500 path runs.

        Args:
            _request: Unused. The route contract requires it.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError("boom")

    async def missing(_request: Request) -> Response:
        """Raise a domain 404 that must not use the unhandled handler.

        Args:
            _request: Unused. The route contract requires it.

        Raises:
            HTTPException: Always, with status 404.
        """
        raise HTTPException(status_code=404, detail="gone")

    async def ok(_request: Request) -> JSONResponse:
        """Return a body the tests ignore.

        Args:
            _request: Unused. The route contract requires it.

        Returns:
            A trivial JSON payload.
        """
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[
            Route("/boom", boom),
            Route("/missing", missing),
            Route("/ok", ok),
        ],
    )
    app.add_exception_handler(
        Exception,
        make_unhandled_http_exception_handler(log_manager.get_child_logger("uvicorn")),
    )
    app.add_middleware(CorrelationIdMiddleware)
    return app


@pytest.fixture
def app(log_manager: LogManager) -> Starlette:
    """Build the tiny app wrapped like production's exception path.

    Args:
        log_manager: Manager the ``uvicorn`` handler logs through.

    Returns:
        An application exposing ``GET /boom``, ``GET /missing``, and ``GET /ok``.
    """
    return build_unhandled_exception_app(log_manager)


@pytest.fixture
async def client(app: Starlette) -> AsyncGenerator[AsyncClient]:
    """Provide a client that does not re-raise app exceptions.

    Args:
        app: The application to send requests to.

    Yields:
        A client bound to that application.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://unhandled.test",
    ) as http_client:
        yield http_client
