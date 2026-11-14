# config

`AppConfig` composes shared loaders. It is not a `BaseSettings` root. This app has no Postgres.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)

## Belongs here

- `APP_NAME` (`notes_mcp`), the MCP server name and instructions, and tenant and user headers.
- `load_app_config()`, which calls the shared loaders and the production logging check.

## Does not belong here

- Redis, logger, server, MCP path, and Prometheus models. Those are `shared_config`.
- Probe and metrics paths. Those are `shared_config`.
- Request-id header names. Those are `shared_middlewares`.
