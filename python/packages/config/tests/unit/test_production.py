"""Production rules that span the environment and one other model."""

from typing import Literal

import pytest
from pydantic import SecretStr

from shared_config import (
    Environment,
    LoggerConfig,
    LogLevel,
    PostgresConfig,
    validate_logger_for_environment,
    validate_postgres_for_environment,
)

_SslMode = Literal["disable", "require", "verify-full"]


def _postgres(ssl_mode: _SslMode) -> PostgresConfig:
    """Minimal Postgres settings so the SSL check has a mode to read."""
    return PostgresConfig(
        HOST="127.0.0.1",
        DATABASE="fruits",
        USER="app",
        PASSWORD=SecretStr("secret"),
        SSL_MODE=ssl_mode,
    )


def test_debug_logging_is_rejected_in_production() -> None:
    """The error names the prefixed variable the operator actually set."""
    logger = LoggerConfig(MIN_LOG_LEVEL=LogLevel.DEBUG)
    with pytest.raises(ValueError, match="BILLING_API__LOGGER__MIN_LOG_LEVEL"):
        validate_logger_for_environment(Environment.PROD, logger, app_name="billing_api")


def test_debug_logging_is_allowed_outside_production() -> None:
    """Local and dev keep debug available."""
    logger = LoggerConfig(MIN_LOG_LEVEL=LogLevel.DEBUG)
    validate_logger_for_environment(Environment.LOCAL, logger, app_name="billing_api")


def test_info_logging_is_allowed_in_production() -> None:
    """The production ban is debug, not every level below error."""
    logger = LoggerConfig(MIN_LOG_LEVEL=LogLevel.INFO)
    validate_logger_for_environment(Environment.PROD, logger, app_name="billing_api")


def test_logger_check_rejects_a_bad_app_name_before_the_environment_matters() -> None:
    """A typo in the app name fails even when the level would otherwise be legal."""
    logger = LoggerConfig()
    with pytest.raises(ValueError, match="app name"):
        validate_logger_for_environment(Environment.LOCAL, logger, app_name="Billing")


def test_disabled_ssl_is_rejected_in_production() -> None:
    """The error names the unprefixed server variable."""
    with pytest.raises(ValueError, match="POSTGRES__SSL_MODE"):
        validate_postgres_for_environment(Environment.PROD, _postgres("disable"))


def test_disabled_ssl_is_allowed_outside_production() -> None:
    """Local Compose uses SSL_MODE=disable. That stays legal when ENV is local."""
    validate_postgres_for_environment(Environment.LOCAL, _postgres("disable"))


def test_required_ssl_is_allowed_in_production() -> None:
    """Require is the default and stays valid in prod."""
    validate_postgres_for_environment(Environment.PROD, _postgres("require"))
