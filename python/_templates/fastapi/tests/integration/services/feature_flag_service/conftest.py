"""Assemble a real FeatureFlagService against the session Redis and PostgreSQL."""

import pytest
from prometheus_client import CollectorRegistry
from sqlalchemy import text

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
    postgres_client: PostgresClient,
    redis_client: RedisClient,
    log_manager: LogManager,
    feature_flag_metrics: FeatureFlagMetrics,
) -> FeatureFlagService:
    """Provide the real service wired to the session containers.

    Args:
        postgres_client: Started engine against Testcontainers Postgres.
        redis_client: Started pool against Testcontainers Redis.
        log_manager: Buffer-backed manager from ``tests/conftest.py``.
        feature_flag_metrics: Collectors on this test's private registry.

    Returns:
        A ``FeatureFlagService`` that talks to real Redis and PostgreSQL.
    """
    return FeatureFlagService(
        postgres_client,
        redis_client,
        FeatureFlagConfig(),
        log_manager.get_child_logger("FeatureFlagService"),
        feature_flag_metrics,
    )


@pytest.fixture(autouse=True)
async def _truncate_feature_flags(  # pyright: ignore[reportUnusedFunction]
    postgres_client: PostgresClient,
) -> None:
    """Empty this service's table before every test. Leaves ``alembic_version``.

    Args:
        postgres_client: Started engine for ``TRUNCATE feature_flags``.
    """
    async with postgres_client.create_session() as session:
        await session.execute(text("TRUNCATE feature_flags"))
        await session.commit()
