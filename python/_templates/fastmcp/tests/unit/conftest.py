"""Shared fixtures for in-process unit tests."""

from unittest.mock import AsyncMock

import pytest

from app.state import AppState
from shared_log_manager import LogManager
from shared_redis import RedisClient
from tests.unit.app_state_factory import AppStateFactory, build_app_state


@pytest.fixture
def redis_client() -> AsyncMock:
    """Provide a Redis client whose list methods are awaitable mocks.

    Returns:
        An ``AsyncMock`` specced on ``RedisClient``.
    """
    return AsyncMock(spec=RedisClient)


@pytest.fixture
def make_app_state(log_manager: LogManager) -> AppStateFactory:
    """Provide a factory that builds AppState with an AsyncMock Redis client.

    Args:
        log_manager: Buffer-backed manager shared by every state this factory builds.

    Returns:
        A callable that accepts an optional ``redis`` client and fills in a
        specced AsyncMock when the caller omits it.
    """

    def factory(*, redis: RedisClient | None = None) -> AppState:
        """Build AppState, forwarding only the Redis client the caller supplied.

        Args:
            redis: Injected Redis client, or ``None`` for a specced AsyncMock.

        Returns:
            Frozen application state for a test ASGI app.
        """
        return build_app_state(log_manager, redis=redis)

    return factory
