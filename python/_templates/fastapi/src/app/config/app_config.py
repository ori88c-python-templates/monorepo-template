"""The application's root configuration model."""

from pydantic import BaseModel

from app.config.app_consts import APP_NAME, FEATURE_FLAGS_LOGICAL_KEY
from shared_config import (
    Environment,
    FeatureFlagConfig,
    LoggerConfig,
    PostgresConfig,
    PrometheusConfig,
    RedisConfig,
    ServerConfig,
    create_logger_config,
    create_postgres_config,
    create_server_config,
    load_environment,
    load_feature_flag_config,
    load_prometheus_config,
    load_redis_config,
    validate_logger_for_environment,
    validate_postgres_for_environment,
)


class AppConfig(BaseModel):
    """One process's settings, composed from shared loaders.

    This is not a ``BaseSettings`` root. Unprefixed ``REDIS__*`` and
    ``BILLING_API__SERVER__*`` cannot share one settings tree.

    Attributes:
        ENV: The deployment environment.
        server: HTTP server bind settings. ``PORT`` is required.
        logger: Structured logging settings.
        redis: Redis connection settings.
        postgres: PostgreSQL connection settings for the feature-flags database.
        feature_flag: Feature-flag cache settings.
        prometheus: Scrape-endpoint settings.
    """

    ENV: Environment
    server: ServerConfig
    logger: LoggerConfig
    redis: RedisConfig
    postgres: PostgresConfig
    feature_flag: FeatureFlagConfig
    prometheus: PrometheusConfig


def load_app_config() -> AppConfig:
    """Load this app's settings from the repo-root env file and the process environment.

    Returns:
        Validated settings. Production rules that span models have already run.

    Raises:
        ValueError: If ``ENV`` is ``prod`` and logging or Postgres SSL is unsafe.
        ValidationError: If a required value is missing or invalid.
        FileNotFoundError: If repo-root discovery fails.
    """
    config = AppConfig(
        ENV=load_environment(),
        server=create_server_config(APP_NAME),
        logger=create_logger_config(APP_NAME),
        redis=load_redis_config(),
        postgres=create_postgres_config(FEATURE_FLAGS_LOGICAL_KEY),
        feature_flag=load_feature_flag_config(),
        prometheus=load_prometheus_config(),
    )
    validate_logger_for_environment(config.ENV, config.logger, app_name=APP_NAME)
    validate_postgres_for_environment(config.ENV, config.postgres)
    return config
