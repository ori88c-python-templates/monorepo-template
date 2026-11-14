"""The application's root configuration model."""

from pydantic import BaseModel

from app.config.app_consts import APP_NAME
from shared_config import (
    Environment,
    LoggerConfig,
    McpConfig,
    PrometheusConfig,
    RedisConfig,
    ServerConfig,
    create_logger_config,
    create_mcp_config,
    create_server_config,
    load_environment,
    load_prometheus_config,
    load_redis_config,
    validate_logger_for_environment,
)


class AppConfig(BaseModel):
    """One process's settings, composed from shared loaders.

    This is not a ``BaseSettings`` root. Unprefixed ``REDIS__*`` and
    ``NOTES_MCP__SERVER__*`` cannot share one settings tree. This app has no
    Postgres, so it does not load a database or check SSL.

    Attributes:
        ENV: The deployment environment.
        server: HTTP bind settings. ``PORT`` is required.
        logger: Structured logging settings.
        redis: Redis connection settings.
        mcp: Streamable HTTP path and SSE response flag.
        prometheus: Scrape-endpoint settings.
    """

    ENV: Environment
    server: ServerConfig
    logger: LoggerConfig
    redis: RedisConfig
    mcp: McpConfig
    prometheus: PrometheusConfig


def load_app_config() -> AppConfig:
    """Load this app's settings from the repo-root env file and the process environment.

    Returns:
        Validated settings. The production logging check has already run.

    Raises:
        ValueError: If ``ENV`` is ``prod`` and logging is unsafe.
        ValidationError: If a required value is missing or invalid.
        FileNotFoundError: If repo-root discovery fails.
    """
    config = AppConfig(
        ENV=load_environment(),
        server=create_server_config(APP_NAME),
        logger=create_logger_config(APP_NAME),
        redis=load_redis_config(),
        mcp=create_mcp_config(APP_NAME),
        prometheus=load_prometheus_config(),
    )
    validate_logger_for_environment(config.ENV, config.logger, app_name=APP_NAME)
    return config
