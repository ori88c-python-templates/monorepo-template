"""Postgres model rules and the logical-database inventory."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from shared_config import PostgresConfig, create_postgres_config

_HOST = "127.0.0.1"
_DATABASE = "app"
_USER = "app"
_PASSWORD = SecretStr("secret")


def _config(
    *,
    connect_timeout_seconds: int = 5,
    statement_timeout_ms: int = 5000,
    pool_timeout_seconds: int = 30,
) -> PostgresConfig:
    """Build a valid model with the timeout knobs a test wants to vary."""
    return PostgresConfig(
        HOST=_HOST,
        DATABASE=_DATABASE,
        USER=_USER,
        PASSWORD=_PASSWORD,
        CONNECT_TIMEOUT_SECONDS=connect_timeout_seconds,
        STATEMENT_TIMEOUT_MS=statement_timeout_ms,
        POOL_TIMEOUT_SECONDS=pool_timeout_seconds,
    )


def _server_lines(*, fruits: str = "fruits_local", people: str | None = "people_local") -> str:
    """Shared server settings plus one or two inventory entries."""
    lines = [
        "POSTGRES__HOST=127.0.0.1",
        "POSTGRES__USER=app",
        "POSTGRES__PASSWORD=s3cret",
        f"POSTGRES__FRUITS__DATABASE={fruits}",
    ]
    if people is not None:
        lines.append(f"POSTGRES__PEOPLE__DATABASE={people}")
    return "\n".join(lines) + "\n"


def test_timeouts_use_documented_defaults() -> None:
    """Omitted timeouts still bound a hung server or pool wait."""
    config = _config()
    assert config.CONNECT_TIMEOUT_SECONDS == 5
    assert config.STATEMENT_TIMEOUT_MS == 5000
    assert config.POOL_TIMEOUT_SECONDS == 30


def test_timeouts_below_one_are_rejected() -> None:
    """Zero would disable the bound; sub-unit values are not useful here."""
    with pytest.raises(ValidationError):
        _config(connect_timeout_seconds=0)
    with pytest.raises(ValidationError):
        _config(statement_timeout_ms=0)
    with pytest.raises(ValidationError):
        _config(pool_timeout_seconds=0)


def test_constructed_timeouts_round_trip() -> None:
    """An explicit triple is stored as given so the engine can apply each knob."""
    config = _config(
        connect_timeout_seconds=3,
        statement_timeout_ms=7000,
        pool_timeout_seconds=15,
    )
    assert config.CONNECT_TIMEOUT_SECONDS == 3
    assert config.STATEMENT_TIMEOUT_MS == 7000
    assert config.POOL_TIMEOUT_SECONDS == 15


def test_connect_args_maps_timeouts_for_the_app_engine() -> None:
    """The application engine gets libpq options; Alembic must not reuse this dict."""
    config = _config(connect_timeout_seconds=3, statement_timeout_ms=7000)
    assert config.connect_args == {
        "connect_timeout": 3,
        "options": "-c statement_timeout=7000",
    }
    assert "connect_args" not in config.model_dump()


def test_dsn_encodes_credentials_and_dump_does_not() -> None:
    """The URL carries sslmode and encoded secrets. model_dump does not."""
    config = PostgresConfig(
        HOST=_HOST,
        DATABASE=_DATABASE,
        USER="app@ops",
        PASSWORD=SecretStr("p@ss/word"),
        SSL_MODE="require",
    )
    rendered = str(config.DSN)
    assert rendered.startswith("postgresql+psycopg://")
    assert "app%40ops" in rendered
    assert "p%40ss%2Fword" in rendered
    assert "sslmode=require" in rendered
    dumped = config.model_dump()
    assert "DSN" not in dumped
    assert "p@ss/word" not in str(dumped)


def test_physical_name_comes_from_the_inventory_entry(tmp_path: Path) -> None:
    """The logical key selects the variable. The value is the physical name."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(), encoding="utf-8")
    fruits = create_postgres_config("fruits", env_file=env_file)
    people = create_postgres_config("people", env_file=env_file)
    assert fruits.DATABASE == "fruits_local"
    assert people.DATABASE == "people_local"
    assert fruits.HOST == people.HOST == "127.0.0.1"
    assert fruits.PASSWORD.get_secret_value() == "s3cret"


def test_two_callers_sharing_one_key_see_the_same_database(tmp_path: Path) -> None:
    """Passing fruits twice does not invent a second database."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(people=None), encoding="utf-8")
    first = create_postgres_config("fruits", env_file=env_file)
    second = create_postgres_config("fruits", env_file=env_file)
    assert first.DATABASE == second.DATABASE == "fruits_local"


def test_missing_inventory_entry_is_rejected(tmp_path: Path) -> None:
    """A key with no POSTGRES__<KEY>__DATABASE fails instead of defaulting to the key."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(people=None), encoding="utf-8")
    with pytest.raises(ValueError, match="POSTGRES__PEOPLE__DATABASE"):
        create_postgres_config("people", env_file=env_file)


def test_bare_database_variable_in_the_file_is_rejected(tmp_path: Path) -> None:
    """POSTGRES__DATABASE cannot name one database for every app."""
    env_file = tmp_path / ".env"
    text = _server_lines(people=None) + "POSTGRES__DATABASE=app\n"
    env_file.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="POSTGRES__DATABASE"):
        create_postgres_config("fruits", env_file=env_file)


def test_bare_database_variable_in_the_process_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A shell export of POSTGRES__DATABASE is the same mistake as a file entry."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(people=None), encoding="utf-8")
    monkeypatch.setenv("POSTGRES__DATABASE", "app")
    with pytest.raises(ValueError, match="POSTGRES__DATABASE"):
        create_postgres_config("fruits", env_file=env_file)


def test_process_environment_overrides_the_physical_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A launch script can point fruits at a different physical database."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(people=None), encoding="utf-8")
    monkeypatch.setenv("POSTGRES__FRUITS__DATABASE", "fruits_ci")
    assert create_postgres_config("fruits", env_file=env_file).DATABASE == "fruits_ci"


def test_invalid_logical_key_is_rejected(tmp_path: Path) -> None:
    """The key has to be safe as an env segment and as a package directory."""
    env_file = tmp_path / ".env"
    env_file.write_text(_server_lines(people=None), encoding="utf-8")
    with pytest.raises(ValueError, match="logical database key"):
        create_postgres_config("Fruits", env_file=env_file)
