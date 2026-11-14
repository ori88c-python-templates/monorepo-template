"""Per-app logger settings and defaults."""

from pathlib import Path

from shared_config import LoggerConfig, LogLevel, create_logger_config


def test_uvicorn_access_logs_default_to_enabled() -> None:
    """Unset matches uvicorn: access lines are installed."""
    config = LoggerConfig()
    assert config.MIN_LOG_LEVEL is LogLevel.INFO
    assert config.ENABLE_UVICORN_ACCESS_LOGS is True


def test_uvicorn_access_logs_can_be_disabled() -> None:
    """The flag is stored as given so the composition root can pass it to uvicorn."""
    config = LoggerConfig(ENABLE_UVICORN_ACCESS_LOGS=False)
    assert config.ENABLE_UVICORN_ACCESS_LOGS is False


def test_two_apps_can_log_at_different_levels(tmp_path: Path) -> None:
    """One shared env file still lets one app run at debug and another at warning."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BILLING_API__LOGGER__MIN_LOG_LEVEL=debug",
                "BILLING_API__LOGGER__ENABLE_UVICORN_ACCESS_LOGS=false",
                "PEOPLE_API__LOGGER__MIN_LOG_LEVEL=warning",
            ]
        ),
        encoding="utf-8",
    )
    billing = create_logger_config("billing_api", env_file=env_file)
    people = create_logger_config("people_api", env_file=env_file)
    assert billing.MIN_LOG_LEVEL is LogLevel.DEBUG
    assert billing.ENABLE_UVICORN_ACCESS_LOGS is False
    assert people.MIN_LOG_LEVEL is LogLevel.WARNING
    assert people.ENABLE_UVICORN_ACCESS_LOGS is True
