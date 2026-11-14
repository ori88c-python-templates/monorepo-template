"""Redis model rules and the unprefixed REDIS__ loader."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from shared_config import RedisConfig, load_redis_config


def test_timeouts_default_to_five_seconds() -> None:
    """Omitted timeouts still bound a hung socket instead of blocking forever."""
    config = RedisConfig(HOST="127.0.0.1")
    assert config.CONNECT_TIMEOUT_SECONDS == 5
    assert config.COMMAND_TIMEOUT_SECONDS == 5


def test_timeouts_below_one_second_are_rejected() -> None:
    """Zero would mean no wait; redis-py treats 0 as a bound of zero."""
    with pytest.raises(ValidationError):
        RedisConfig(HOST="127.0.0.1", CONNECT_TIMEOUT_SECONDS=0)
    with pytest.raises(ValidationError):
        RedisConfig(HOST="127.0.0.1", COMMAND_TIMEOUT_SECONDS=0)


def test_constructed_timeouts_round_trip() -> None:
    """An explicit pair is stored as given so the client can apply both knobs."""
    config = RedisConfig(HOST="127.0.0.1", CONNECT_TIMEOUT_SECONDS=3, COMMAND_TIMEOUT_SECONDS=7)
    assert config.CONNECT_TIMEOUT_SECONDS == 3
    assert config.COMMAND_TIMEOUT_SECONDS == 7


def test_dsn_encodes_the_password_and_dump_does_not() -> None:
    """The URL is a property, so serialising the model cannot leak the secret."""
    config = RedisConfig(HOST="redis.internal", PASSWORD=SecretStr("p@ss/word"))
    assert "p%40ss%2Fword" in str(config.DSN)
    assert config.DSN.scheme == "redis"
    dumped = config.model_dump()
    assert "DSN" not in dumped
    assert "p@ss/word" not in str(dumped)
    assert config.PASSWORD is not None
    assert config.PASSWORD.get_secret_value() == "p@ss/word"


def test_tls_selects_the_rediss_scheme() -> None:
    """USE_TLS is the only switch for the scheme."""
    assert RedisConfig(HOST="redis.internal", USE_TLS=True).DSN.scheme == "rediss"


def test_loader_reads_redis_block(tmp_path: Path) -> None:
    """REDIS__* fills the shared connection, including an explicit password."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "REDIS__HOST=redis.internal",
                "REDIS__PORT=6380",
                "REDIS__DB=2",
                "REDIS__PASSWORD=secret",
                "REDIS__USE_TLS=true",
                "REDIS__CONNECT_TIMEOUT_SECONDS=3",
                "REDIS__COMMAND_TIMEOUT_SECONDS=4",
            ]
        ),
        encoding="utf-8",
    )
    config = load_redis_config(env_file=env_file)
    assert config.HOST == "redis.internal"
    assert config.PORT == 6380
    assert config.DB == 2
    assert config.PASSWORD is not None
    assert config.PASSWORD.get_secret_value() == "secret"
    assert config.USE_TLS is True
    assert config.CONNECT_TIMEOUT_SECONDS == 3
    assert config.COMMAND_TIMEOUT_SECONDS == 4


def test_empty_password_is_not_unset(tmp_path: Path) -> None:
    """An empty REDIS__PASSWORD is an empty secret, not an unauthenticated server."""
    env_file = tmp_path / ".env"
    env_file.write_text("REDIS__HOST=127.0.0.1\nREDIS__PASSWORD=\n", encoding="utf-8")
    config = load_redis_config(env_file=env_file)
    assert config.PASSWORD is not None
    assert config.PASSWORD.get_secret_value() == ""


def test_missing_host_is_rejected(tmp_path: Path) -> None:
    """A deployment that forgets REDIS__HOST fails before the first command."""
    env_file = tmp_path / ".env"
    env_file.write_text("REDIS__PORT=6379\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_redis_config(env_file=env_file)
