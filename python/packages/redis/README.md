# shared-redis

One Redis connection for a process. Key helpers always start with the app name.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Keys](#keys)
- [Exports](#exports)
- [Testing](#testing)

## Belongs here

- `RedisClient`: lazy pool, `start`, `stop`, `ping`, and `raw`.
- `get_string`, `set_string`, `append_list_item`, and `read_list`. Each takes the key parts after the app name and encodes them with `create_redis_key`.
- `create_redis_key`, the length-prefix encoding that keeps a colon inside a part from merging with the next part.

The composition root injects a child logger. This client does not build one.

## Does not belong here

- Feature-flag or notes logic. Those are services owned by an app.
- A second connection. One client is one `RedisConfig`.

## Keys

`RedisClient` is constructed with `app_name`, which must pass `validate_app_name` (`billing_api`, not `billing-api`).

```python
await client.get_string("feature_flag", tenant_id, name)
await client.set_string("feature_flag", tenant_id, name, value="1", ttl_seconds=300)
```

`raw` does not add the prefix. A key passed to `raw` is the caller's responsibility. Prefer the helpers.

## Exports

Import from `shared_redis`:

- `RedisClient`
- `create_redis_key`

## Testing

This package's tests request the `log_manager` fixture and pass `log_manager.get_child_logger("RedisClient")`. Do not construct a `LogManager`. Pass a pre-built redis-py client when the test must not open a socket. Those tests assert the encoded key. `start`, `stop`, and `ping` stay integration tests against a real server.

App service tests do not take a double from this package. There is no `shared_redis.testing`, and no pytest plugin fixture named `redis_client`. Integration tests use that name for a real client.

The app's `tests/unit/conftest.py` owns one fixture. Every service in that app requests it. A second service does not build its own. An app that currently builds the mock beside a single service lifts it to that conftest when a second consumer appears.

```python
@pytest.fixture
def redis_client() -> AsyncMock:
    return AsyncMock(spec=RedisClient)
```

Each test sets `return_value` or `side_effect`. Service tests pass key parts. They do not call `create_redis_key`. Encoding is this package's test.

```python
redis_client.get_string.return_value = None
redis_client.get_string.assert_awaited_once_with("feature_flag", tenant_id, name)
redis_client.set_string.assert_awaited_once_with(
    "feature_flag", tenant_id, name, value=payload, ttl_seconds=300
)
```
