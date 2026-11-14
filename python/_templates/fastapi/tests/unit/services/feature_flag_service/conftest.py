"""Assemble a real FeatureFlagService from the shared client doubles."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from prometheus_client import CollectorRegistry

from app.metrics import FeatureFlagMetrics
from app.services import FeatureFlagService
from shared_config import FeatureFlagConfig
from shared_log_manager import LogManager
from shared_postgres import PostgresClient
from shared_redis import RedisClient


@pytest.fixture
def collector_registry() -> CollectorRegistry:
    """Provide a private collector so metric tests cannot collide.

    Returns:
        An empty registry bound to this test's ``FeatureFlagMetrics``.
    """
    return CollectorRegistry()


@pytest.fixture
def feature_flag_metrics(collector_registry: CollectorRegistry) -> FeatureFlagMetrics:
    """Provide collectors registered on the test's private registry.

    Args:
        collector_registry: Empty registry for this test.

    Returns:
        Metrics the service under test will increment.
    """
    return FeatureFlagMetrics(registry=collector_registry)


@pytest.fixture
def feature_flag_service(
    postgres_client: MagicMock,
    redis_client: AsyncMock,
    log_manager: LogManager,
    feature_flag_metrics: FeatureFlagMetrics,
) -> FeatureFlagService:
    """Provide the real service wired to mocked Redis and PostgreSQL.

    Args:
        postgres_client: Sync ``create_session`` returning the shared session mock.
        redis_client: Client whose string get and set are awaitable mocks.
        log_manager: Buffer-backed manager from the unit-test root.
        feature_flag_metrics: Collectors on this test's private registry.

    Returns:
        A ``FeatureFlagService`` that never opens a socket.
    """
    return FeatureFlagService(
        cast(PostgresClient, postgres_client),
        cast(RedisClient, redis_client),
        FeatureFlagConfig(),
        log_manager.get_child_logger("FeatureFlagService"),
        feature_flag_metrics,
    )
