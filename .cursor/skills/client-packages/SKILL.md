---
name: client-packages
description: >-
  Decide whether a client, adapter, or service belongs in python/packages or
  stays in one app. Use when the user asks to add a client, share a service,
  extract a library, or move GithubClient, FeatureFlagService, or
  CsvReportWriter.
---

# Client packages

A client for an external resource lives in `python/packages/`, even when only one app uses it. Postgres, Redis, and GitHub are the examples. Its settings model lives in `shared_config`. It is not named `shared_*` unless every app category uses it. `shared_*` is cross-app infrastructure such as `shared_redis`. A package that imports one framework uses that framework's name, as `fastapi_middlewares` does.

`python/packages/github_client` is the one-app client. `GithubClient`, `GithubAdapter`, `GithubRepoInfo`, and `GithubOrganizationNotFoundError` stay together. `GithubClientConfig` and `load_github_client_config` live in `shared_config`. The client takes `app_name` from `validate_app_name` and sends it as the user agent. The task-runner blueprint depends on the client. A blueprint that does not call GitHub does not.

A service owned by one app stays in that app. `python/_templates/fastapi/src/app/services/feature_flag/feature_flag_service.py` is `FeatureFlagService`. It is never a package. `python/_templates/task_runner/src/app/services/report/csv_report_writer.py` is `CsvReportWriter`: it may import `GithubRepoInfo` and it still stays in the app. `TaskRunner` and `LifecycleManager` stay in the app. `cancel_on_sigterm` stays in the app lifecycle.

`feature_flags_db` holds the `feature_flags` table and its Alembic history. `shared_postgres` is the connection only. Adding that database package follows `.cursor/skills/alembic/SKILL.md`.

## Tests

Tests move with the client into `tests/<module>/test_<feature>.py`. They do not keep the app path `tests/unit/<layer>/...`. The app does not keep a second copy and does not import the package's tests.

`tests/` and `tests/<module>/` have no `__init__.py`. A second top-level `tests` package collides during collection. `tests/` is not on `pythonpath`. A fake lives in `tests/fakes/` when the package needs one, and that directory is the `pythonpath` entry.

A client package does not export test doubles and does not register a pytest plugin. `shared_log_manager.testing` is the exception, because constructing `LogManager` installs process handlers. The live GitHub search stays in the client package, marked `integration`. A skip is not a pass.
