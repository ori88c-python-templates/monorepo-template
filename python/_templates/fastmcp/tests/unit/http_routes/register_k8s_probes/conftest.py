"""Shared fixtures for the Kubernetes probe tests."""

from collections.abc import AsyncGenerator
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette

from app.http_routes import register_k8s_probes
from app.state import APP_STATE_ATTRIBUTE
from shared_redis import RedisClient
from tests.unit.app_state_factory import AppStateFactory


def _probe_app_with_clients(
    make_app_state: AppStateFactory,
    redis_client: AsyncMock,
    *,
    include_in_schema: bool = True,
) -> Starlette:
    """Register the probes on an app whose Redis ping behaves as requested.

    Args:
        make_app_state: Shared factory that fills AppState with injected doubles.
        redis_client: Unit-test Redis double. ``ping`` is already awaitable.
        include_in_schema: Whether probe paths are marked for schema. Staging and
            production register with this false.

    Returns:
        An application with ``AppState`` attached so ``/readyz`` can reach Redis.
    """
    mcp = FastMCP("probes")
    register_k8s_probes(mcp, include_in_schema=include_in_schema)
    app = mcp.http_app(stateless_http=True, json_response=True, host_origin_protection=False)
    setattr(
        app.state,
        APP_STATE_ATTRIBUTE,
        make_app_state(redis=cast(RedisClient, redis_client)),
    )
    return app


@pytest.fixture
def probe_app() -> Starlette:
    """Build an application carrying the probes and nothing else.

    Deliberately not the real application. Registering the probes on a bare server
    means no configuration, no state and no clients exist, so any test that passes
    has proved liveness depends on none of them.

    Returns:
        An application exposing the probe endpoints.
    """
    mcp = FastMCP("probes")
    register_k8s_probes(mcp, include_in_schema=True)
    return mcp.http_app(stateless_http=True, json_response=True, host_origin_protection=False)


@pytest.fixture
async def probe_client(probe_app: Starlette) -> AsyncGenerator[AsyncClient]:
    """Provide a client that speaks ASGI directly to ``probe_app``.

    Requests go through the real routing stack, but over an in-process transport
    rather than a socket. ``ASGITransport`` does not run the lifespan, which is
    the point: liveness is exercised against an application that was never started.

    Args:
        probe_app: The application to send requests to.

    Yields:
        A client bound to that application.
    """
    async with AsyncClient(
        transport=ASGITransport(app=probe_app),
        base_url="http://probes.test",
    ) as client:
        yield client


@pytest.fixture
def ready_app(make_app_state: AppStateFactory, redis_client: AsyncMock) -> Starlette:
    """Build a probe app whose Redis ping succeeds.

    Args:
        make_app_state: Shared factory that fills AppState with injected doubles.
        redis_client: Unit-test Redis double.

    Returns:
        An application with a healthy mocked Redis client on ``AppState``.
    """
    return _probe_app_with_clients(make_app_state, redis_client)


@pytest.fixture
def schema_hidden_probe_app(
    make_app_state: AppStateFactory,
    redis_client: AsyncMock,
) -> Starlette:
    """Register probes with schema inclusion off, as staging and production do.

    Args:
        make_app_state: Shared factory that fills AppState with injected doubles.
        redis_client: Unit-test Redis double.

    Returns:
        An application whose probe paths are served but omitted from schema.
    """
    return _probe_app_with_clients(make_app_state, redis_client, include_in_schema=False)


@pytest.fixture
async def ready_client(ready_app: Starlette) -> AsyncGenerator[AsyncClient]:
    """Provide a client that speaks ASGI directly to ``ready_app``.

    Args:
        ready_app: The application to send requests to.

    Yields:
        A client bound to that application.
    """
    async with AsyncClient(
        transport=ASGITransport(app=ready_app),
        base_url="http://probes.test",
    ) as client:
        yield client


@pytest.fixture
def redis_down_app(make_app_state: AppStateFactory, redis_client: AsyncMock) -> Starlette:
    """Build a probe app whose Redis ping fails.

    Args:
        make_app_state: Shared factory that fills AppState with injected doubles.
        redis_client: Unit-test Redis double.

    Returns:
        An application whose readiness check cannot succeed.
    """
    redis_client.ping.side_effect = ConnectionError("redis down")
    return _probe_app_with_clients(make_app_state, redis_client)


@pytest.fixture
async def redis_down_client(redis_down_app: Starlette) -> AsyncGenerator[AsyncClient]:
    """Provide a client bound to ``redis_down_app``.

    Args:
        redis_down_app: The application to send requests to.

    Yields:
        A client bound to that application.
    """
    async with AsyncClient(
        transport=ASGITransport(app=redis_down_app),
        base_url="http://probes.test",
    ) as client:
        yield client
