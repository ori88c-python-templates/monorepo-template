"""Checks that span more than one resource model.

Each app calls the helpers that match the models it composed. An app with no
Postgres does not call :func:`validate_postgres_for_environment`.
"""

from shared_config.environment import Environment
from shared_config.logger_config import LoggerConfig, LogLevel
from shared_config.names import validate_app_name
from shared_config.postgres_config import PostgresConfig


def validate_logger_for_environment(
    environment: Environment,
    logger: LoggerConfig,
    *,
    app_name: str,
) -> None:
    """Reject debug logging in production for one app.

    Args:
        environment: Deployment environment from :func:`load_environment`.
        logger: That app's logger settings.
        app_name: App directory name. The error cites ``<APP>__LOGGER__MIN_LOG_LEVEL``.

    Raises:
        ValueError: If ``app_name`` is not an identifier, or if the level is debug
            while ``environment`` is production.
    """
    prefix = validate_app_name(app_name).upper()
    if environment is not Environment.PROD:
        return
    if logger.MIN_LOG_LEVEL is LogLevel.DEBUG:
        message = (
            f"{prefix}__LOGGER__MIN_LOG_LEVEL=debug is not allowed when ENV=prod: "
            "debug logging risks writing sensitive payloads to the log stream."
        )
        raise ValueError(message)


def validate_postgres_for_environment(
    environment: Environment,
    postgres: PostgresConfig,
) -> None:
    """Reject unencrypted Postgres in production.

    Args:
        environment: Deployment environment from :func:`load_environment`.
        postgres: Settings for the database this app selected.

    Raises:
        ValueError: If SSL is disabled while ``environment`` is production.
    """
    if environment is not Environment.PROD:
        return
    if postgres.SSL_MODE == "disable":
        message = (
            "POSTGRES__SSL_MODE=disable is not allowed when ENV=prod: "
            "database traffic must be encrypted in production."
        )
        raise ValueError(message)
