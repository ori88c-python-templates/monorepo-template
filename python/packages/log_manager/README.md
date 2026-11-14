# shared-log-manager

Injectable structured logging. One `LogManager` per process is built by the composition root and handed to whatever needs a logger. The class is not a singleton, and it never calls `structlog.configure()`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)
- [Testing](#testing)

## Belongs here

- `LogManager`. Construct it with a `LoggerConfig`, an `Environment`, an `app_version`, and a non-empty `app_name`. `app_name` is the `app` field on every record. It may contain hyphens. It is not the env-prefix name (`billing_api`).
- `get_child_logger(name)`. The name is the `context` field. Pass that child into the component. Do not keep a module-level logger.
- Bridges that turn stdlib loggers into children of `LogManager`. They attach a handler to a logger name. They do not import FastAPI, FastMCP, or uvicorn.
  - `install_uvicorn_error_logging` and `install_uvicorn_access_logging`
  - `install_fastmcp_logging` for the stdlib logger named `fastmcp`. A FastAPI app simply does not call it.
  - `install_stdlib_log_bridge` for the root stdlib logger, at WARNING, recording `stdlib_logger`. A task runner calls it. A FastAPI or FastMCP app does not: their named bridges already set `propagate = False`.
  - `UvicornLogHandler`, `StdlibLogHandler`, and `UvicornAsgiExceptionFilter`
  - `make_asyncio_exception_handler` and `make_sys_excepthook`

## Does not belong here

- `LoggerConfig` and `Environment`. Those stay in `shared_config`.
- A global logger, a process-wide `structlog.configure()`, or a dependency on FastAPI or FastMCP.

## Exports

Import from `shared_log_manager`:

- `LogManager`
- `UvicornLogHandler`, `UvicornAsgiExceptionFilter`
- `install_uvicorn_access_logging`, `install_uvicorn_error_logging`, `install_fastmcp_logging`, `install_stdlib_log_bridge`
- `StdlibLogHandler`
- `make_asyncio_exception_handler`, `make_sys_excepthook`

## Testing

Other packages test components that take a child logger by using this package. Do not build a second fixture and do not copy the JSON reader.

- Request the `log_manager` fixture. This package registers it with pytest. A local `conftest.py` does not build another manager.
- Pass `log_manager.get_child_logger("Name")` into the component. `Name` is the log `context`.
- Request `sink` when the test needs the buffer. Read the lines with `read_records` imported from `shared_log_manager.testing`. Do not copy that function.
- Request `make_manager` only to change the level, environment, app name, app version, or stream. The default `log_manager` fixture already uses `Environment.DEV`, `app_version="0.1.0"`, and `app_name="billing-api"`.
- Do not call `LogManager(...)` in a test. This package's own suite has two exceptions: the test that an empty `app_name` is rejected, and the stdout subprocess scripts, which cannot see a fixture.
- Production code imports `shared_log_manager`. It does not import `shared_log_manager.testing`.
