"""Reusable sub-config models and the loaders that read the repo-root env file.

Apps compose these into their own ``AppConfig``. This package does not define one:
a single ``BaseSettings`` root cannot mix unprefixed ``REDIS__*`` with
``BILLING_API__SERVER__*``.
"""

from shared_config.environment import Environment, load_environment
from shared_config.feature_flag_config import FeatureFlagConfig, load_feature_flag_config
from shared_config.github_client_config import GithubClientConfig, load_github_client_config
from shared_config.infrastructure_paths import LIVEZ_ENDPOINT, METRICS_ENDPOINT, READYZ_ENDPOINT
from shared_config.loading import load_app_resource, repo_root
from shared_config.logger_config import LoggerConfig, LogLevel, create_logger_config
from shared_config.mcp_config import McpConfig, create_mcp_config
from shared_config.names import validate_app_name
from shared_config.postgres_config import PostgresConfig, create_postgres_config
from shared_config.production import (
    validate_logger_for_environment,
    validate_postgres_for_environment,
)
from shared_config.prometheus_config import PrometheusConfig, load_prometheus_config
from shared_config.redis_config import RedisConfig, load_redis_config
from shared_config.server_config import ServerConfig, create_server_config

__all__ = [
    "LIVEZ_ENDPOINT",
    "METRICS_ENDPOINT",
    "READYZ_ENDPOINT",
    "Environment",
    "FeatureFlagConfig",
    "GithubClientConfig",
    "LogLevel",
    "LoggerConfig",
    "McpConfig",
    "PostgresConfig",
    "PrometheusConfig",
    "RedisConfig",
    "ServerConfig",
    "create_logger_config",
    "create_mcp_config",
    "create_postgres_config",
    "create_server_config",
    "load_app_resource",
    "load_environment",
    "load_feature_flag_config",
    "load_github_client_config",
    "load_prometheus_config",
    "load_redis_config",
    "repo_root",
    "validate_app_name",
    "validate_logger_for_environment",
    "validate_postgres_for_environment",
]
