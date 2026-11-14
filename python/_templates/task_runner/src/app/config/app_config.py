"""The application's root configuration model."""

from pathlib import Path

from pydantic import BaseModel

from app.config.app_consts import APP_NAME
from app.config.github_report_config import GithubReportConfig, load_github_report_config
from shared_config import (
    Environment,
    GithubClientConfig,
    LoggerConfig,
    create_logger_config,
    load_environment,
    load_github_client_config,
    validate_logger_for_environment,
)
from shared_config.loading import USE_ROOT_ENV, UseRootEnv


class AppConfig(BaseModel):
    """One process's settings, composed from shared loaders.

    This is not a ``BaseSettings`` root. Unprefixed ``ENV`` and
    ``GITHUB_REPORT__GITHUB__*`` cannot share one settings tree.

    Attributes:
        ENV: The deployment environment.
        logger: Structured logging settings.
        github: GitHub organization, token, and timeout.
        github_report: Directory the CSV is written into.
    """

    ENV: Environment
    logger: LoggerConfig
    github: GithubClientConfig
    github_report: GithubReportConfig


def load_app_config(
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> AppConfig:
    """Load this app's settings from the repo-root env file and the process environment.

    Args:
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated settings. The production logging rule has already run.

    Raises:
        ValueError: If ``ENV`` is ``prod`` and logging is debug.
        ValidationError: If a required value is missing or invalid.
        FileNotFoundError: If repo-root discovery fails.
    """
    config = AppConfig(
        ENV=load_environment(env_file=env_file),
        logger=create_logger_config(APP_NAME, env_file=env_file),
        github=load_github_client_config(APP_NAME, env_file=env_file),
        github_report=load_github_report_config(APP_NAME, env_file=env_file),
    )
    validate_logger_for_environment(config.ENV, config.logger, app_name=APP_NAME)
    return config
