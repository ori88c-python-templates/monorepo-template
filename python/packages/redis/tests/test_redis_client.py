"""RedisClient prefixes keys with the app name and passes timeouts through."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis

from shared_config import RedisConfig
from shared_log_manager import LogManager
from shared_redis import RedisClient, create_redis_key


def _config() -> RedisConfig:
    return RedisConfig(
        HOST="127.0.0.1",
        CONNECT_TIMEOUT_SECONDS=3,
        COMMAND_TIMEOUT_SECONDS=7,
    )


def test_from_url_receives_socket_timeouts(log_manager: LogManager) -> None:
    """Construction is lazy: inspecting the pool does not open a socket."""
    client = RedisClient(_config(), log_manager.get_child_logger("RedisClient"), "billing_api")
    kwargs = client.raw.connection_pool.connection_kwargs
    assert kwargs["socket_connect_timeout"] == 3
    assert kwargs["socket_timeout"] == 7
    assert kwargs["retry_on_timeout"] is False


def test_app_name_must_be_an_identifier(log_manager: LogManager) -> None:
    """A hyphenated name would not match the env prefix."""
    with pytest.raises(ValueError, match="app name"):
        RedisClient(_config(), log_manager.get_child_logger("RedisClient"), "billing-api")


def _stand_in() -> tuple[Redis, AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    get = AsyncMock(return_value="stored")
    set_ = AsyncMock()
    rpush = AsyncMock()
    lrange = AsyncMock(return_value=["one", "two"])
    client = MagicMock()
    client.get = get
    client.set = set_
    client.rpush = rpush
    client.lrange = lrange
    return cast(Redis, client), get, set_, rpush, lrange


async def test_helpers_prefix_the_app_name(log_manager: LogManager) -> None:
    """Callers pass parts. The app name is not optional."""
    raw, get, set_, rpush, lrange = _stand_in()
    client = RedisClient(
        _config(),
        log_manager.get_child_logger("RedisClient"),
        "billing_api",
        client=raw,
    )
    expected = create_redis_key("billing_api", "feature_flag", "tenant", "name")

    assert await client.get_string("feature_flag", "tenant", "name") == "stored"
    get.assert_awaited_with(expected)

    await client.set_string("feature_flag", "tenant", "name", value="1", ttl_seconds=30)
    set_.assert_awaited_with(expected, "1", ex=30)

    await client.append_list_item("notes", item="hello")
    rpush.assert_awaited_with(create_redis_key("billing_api", "notes"), "hello")

    assert await client.read_list("notes") == ["one", "two"]
    lrange.assert_awaited_with(create_redis_key("billing_api", "notes"), 0, -1)


async def test_helpers_reject_a_key_with_no_parts(log_manager: LogManager) -> None:
    """The app name alone is not a key the helpers will build."""
    raw, _get, _set, _rpush, _lrange = _stand_in()
    client = RedisClient(
        _config(),
        log_manager.get_child_logger("RedisClient"),
        "billing_api",
        client=raw,
    )
    with pytest.raises(ValueError, match="part"):
        await client.get_string()


def test_raw_is_the_injected_client(log_manager: LogManager) -> None:
    """``raw`` is the stand-in and does not wrap keys."""
    raw, _get, _set, _rpush, _lrange = _stand_in()
    client = RedisClient(
        _config(),
        log_manager.get_child_logger("RedisClient"),
        "billing_api",
        client=raw,
    )
    assert client.raw is raw
