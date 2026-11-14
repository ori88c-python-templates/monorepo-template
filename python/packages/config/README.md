# shared-config

Reusable configuration building blocks. Each app builds its own `AppConfig` from these models and loaders. This package does not define `AppConfig`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Env names](#env-names)
- [Exports](#exports)

## Belongs here

- One model per shared resource: environment, Redis, Postgres, server bind, logger, Prometheus, MCP, and feature-flag TTL.
- Loaders that read the repo-root `.env` by absolute path. The process environment wins over the file. Pass `env_file=None` to ignore files.
- `create_*` loaders for settings that differ per app: server, logger, and MCP. The prefix is the app directory name uppercased, so `billing_api` reads `BILLING_API__SERVER__PORT`.
- `load_*` loaders for settings shared by every process.
- `load_app_resource(model, app_name, resource)` for an app-owned model. It reads `<APP>__<RESOURCE>__*`. The model stays in the app.
- `GithubClientConfig` and `load_github_client_config(app_name)` for a client used by one app. The client package does not own the model.
- Production checks that span models: `validate_logger_for_environment` and `validate_postgres_for_environment`.
- `LIVEZ_ENDPOINT` (`/livez`), `READYZ_ENDPOINT` (`/readyz`), and `METRICS_ENDPOINT` (`/metrics`). These are constants, not env fields. A `.env` typo must not rename a path kubelet or Prometheus already calls.

## Does not belong here

- `AppConfig`. The app composes the pieces and calls the validators it needs. An MCP app with no database does not call the Postgres functions.
- Clients, middleware, or logging. Connection URLs are properties on the models so a dump cannot include a password.

## Env names

- Unprefixed: `ENV`, `REDIS__*`, the Postgres server (`HOST`, `PORT`, `USER`, `PASSWORD`, `SSL_MODE`, timeouts), `PROMETHEUS__SHOULD_GZIP`, `FEATURE_FLAG__CACHE_TTL_SECONDS`.
- Per app: `<APP>__SERVER__*`, `<APP>__LOGGER__*`, `<APP>__MCP__*`, `<APP>__GITHUB__*`. `PORT` has no default. An app-owned model uses the same shape through `load_app_resource`: `<APP>__<RESOURCE>__*`.
- Postgres database names are an inventory: `create_postgres_config("fruits")` reads `POSTGRES__FRUITS__DATABASE`. A bare `POSTGRES__DATABASE` is rejected. The same key shares a database. A missing key fails.

## Exports

Import from `shared_config`:

- `Environment`, `load_environment`
- `RedisConfig`, `load_redis_config`
- `PostgresConfig`, `create_postgres_config`
- `ServerConfig`, `create_server_config`
- `LoggerConfig`, `LogLevel`, `create_logger_config`
- `PrometheusConfig`, `load_prometheus_config`
- `McpConfig`, `create_mcp_config`
- `GithubClientConfig`, `load_github_client_config`
- `FeatureFlagConfig`, `load_feature_flag_config`
- `load_app_resource`
- `validate_app_name`
- `validate_logger_for_environment`, `validate_postgres_for_environment`
- `LIVEZ_ENDPOINT`, `READYZ_ENDPOINT`, `METRICS_ENDPOINT`
- `repo_root`
