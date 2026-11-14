"""Prefixed env keys reach the resource they name."""

from pathlib import Path

from app.config import LogLevel
from tests.load_app_config import load_app_config


def test_nested_keys_reach_their_resource_model(tmp_path: Path) -> None:
    """``GITHUB_REPORT__LOGGER__MIN_LOG_LEVEL`` lands on ``AppConfig.logger``."""
    env_file = tmp_path / ".env"
    env_file.write_text("GITHUB_REPORT__LOGGER__MIN_LOG_LEVEL=error\n", encoding="utf-8")

    config = load_app_config(env_file)

    assert config.logger.MIN_LOG_LEVEL is LogLevel.ERROR


def test_a_foreign_prefix_is_ignored(tmp_path: Path) -> None:
    """One env file holds every app. This process only reads its own prefix."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "REDIS__HOST=127.0.0.1\nGITHUB_REPORT__LOGGER__MIN_LOG_LEVEL=warning\n",
        encoding="utf-8",
    )

    config = load_app_config(env_file)

    assert config.logger.MIN_LOG_LEVEL is LogLevel.WARNING
    assert not hasattr(config, "redis")
