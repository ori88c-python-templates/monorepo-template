# shared-postgres

One async SQLAlchemy engine for a process. Tables are not here.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)
- [Testing](#testing)

## Belongs here

- `PostgresClient`: lazy engine, `create_session`, `start`, `stop`, `ping`, and `raw`.
- Pool settings for the application process: `pool_pre_ping` and `POOL_TIMEOUT_SECONDS`. `connect_args` includes the application's statement timeout.

The composition root injects a child logger and a `PostgresConfig` from `create_postgres_config(logical_key)`.

## Does not belong here

- ORM models, `PostgresBase`, and Alembic. Each database package owns its schema and migration history.
- Services. A service that reads a table lives in the app that owns that behavior.
- Alembic's engine. Migrations use `NullPool` and `CONNECT_TIMEOUT_SECONDS` only. They must not copy this client's `connect_args`.

## Exports

Import from `shared_postgres`:

- `PostgresClient`

## Testing

This package's tests request the `log_manager` fixture and pass `log_manager.get_child_logger("PostgresClient")`. Do not construct a `LogManager`. Pass `engine_creator` when the test must not open a socket. `start`, `stop`, and `ping` stay integration tests against a real server.

App service tests do not take a double from this package. There is no `shared_postgres.testing`.

The app's `tests/unit/conftest.py` owns one `postgres_client`, shared by every service. `create_session` is synchronous. `AsyncMock(spec=PostgresClient)` makes `create_session()` awaitable and breaks `async with`. `session.add` is a `MagicMock` because SQLAlchemy's `add` is not a coroutine. Leaving it on the `AsyncMock` leaks an un-awaited coroutine.

```python
@pytest.fixture
def postgres_session() -> AsyncMock:
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False
    session.add = MagicMock()
    return session


@pytest.fixture
def postgres_client(postgres_session: AsyncMock) -> MagicMock:
    client = MagicMock(spec=PostgresClient)
    client.create_session = MagicMock(return_value=postgres_session)
    return client
```

Services use the real row class with that session and set `postgres_session.get.return_value` in the test.
