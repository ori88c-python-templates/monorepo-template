# config

`AppConfig` composes shared loaders. It is not a `BaseSettings` root.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)

## Belongs here

- `APP_NAME` (`billing_api`), tenant and user headers, and the docs paths.
- `load_app_config()`, which calls the shared loaders and the production checks.

## Does not belong here

- Redis, Postgres, logger, server, Prometheus, and feature-flag cache models. Those are `shared_config`.
- Probe and metrics paths. Those are `shared_config`.
- Request-id header names. Those are `shared_middlewares`.
