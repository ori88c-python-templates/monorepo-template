"""Configuration for structured logging of one app process."""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model
from shared_config.names import validate_app_name


class LogLevel(StrEnum):
    """Log levels accepted by structlog.

    These are exactly structlog's canonical level names, i.e. the values of
    ``structlog._log_levels.LEVEL_TO_NAME``. structlog's ``NAME_TO_LEVEL`` map also
    accepts ``warn``, ``exception`` and ``notset``, but those are aliases rather than
    distinct levels and are deliberately not offered here.

    The enum is declared without importing structlog so that the config package stays
    free of runtime dependencies on the logging implementation.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LoggerConfig(BaseModel):
    """Logging configuration for one app.

    ``LogManager`` applies ``MIN_LOG_LEVEL`` only. Whether uvicorn access lines
    are installed is a composition-root decision in that app. Each app has its own
    ``<APP>__LOGGER__*`` block so one local process can run at debug while another
    stays at info.

    Attributes:
        MIN_LOG_LEVEL: Lowest severity that will be emitted. Records below this level
            are discarded before any processor runs.
        ENABLE_UVICORN_ACCESS_LOGS: When true (uvicorn's default), ``uvicorn.access``
            is bridged into a ``context="uvicorn.access"`` child as JSON. When
            false, ``uvicorn.run(..., access_log=False)`` and no access lines
            are emitted.
    """

    MIN_LOG_LEVEL: LogLevel = LogLevel.INFO
    ENABLE_UVICORN_ACCESS_LOGS: bool = True


def create_logger_config(
    app_name: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> LoggerConfig:
    """Load ``<APP>__LOGGER__*``.

    Args:
        app_name: App directory name, such as ``billing_api``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated logger settings. Unset fields keep the defaults (``info``, access
        logs on).

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier.
        ValidationError: If a value is not a known level or a boolean.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    prefix = f"{validate_app_name(app_name).upper()}__LOGGER__"
    return load_model(LoggerConfig, env_prefix=prefix, env_file=env_file)
