"""Settings that are individually valid but unsafe in production are rejected."""

from pathlib import Path

import pytest

from app.config import Environment, LogLevel
from tests.load_app_config import load_app_config


def test_debug_logging_is_rejected_in_prod(tmp_path: Path) -> None:
    """Debug logging with ``ENV=prod`` fails at startup and names this app's variable."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ENV=prod\nGITHUB_REPORT__LOGGER__MIN_LOG_LEVEL=debug\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="GITHUB_REPORT__LOGGER__MIN_LOG_LEVEL"):
        load_app_config(env_file)


@pytest.mark.parametrize("env", [Environment.LOCAL, Environment.DEV, Environment.STAGING])
def test_debug_logging_is_allowed_outside_prod(tmp_path: Path, env: Environment) -> None:
    """Every non-production environment may log at ``debug``."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"ENV={env.value}\nGITHUB_REPORT__LOGGER__MIN_LOG_LEVEL=debug\n",
        encoding="utf-8",
    )

    config = load_app_config(env_file)

    assert config.ENV is env
    assert config.logger.MIN_LOG_LEVEL is LogLevel.DEBUG
