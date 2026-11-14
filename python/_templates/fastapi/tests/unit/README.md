# unit

In-process tests only.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)

## Belongs here

Dependencies are passed in. The log manager comes from `shared_log_manager.testing`. Redis and Postgres come from the fixtures in `tests/unit/conftest.py`.

Layout mirrors the app package: one directory per area, then one directory per component, then one file per feature.

```
routes/          feature_flag_router, k8s_probe_router, route_child_logger, get_user_details
prometheus/      metrics route is omitted from OpenAPI and still served
services/        feature_flag_service
distribution/    this checkout reports an installed version
```

`tests/unit/conftest.py` owns `redis_client` and `postgres_client`. Probe tests set `ping.side_effect` on those fixtures. Route tests mock `FeatureFlagService`.

## Does not belong here

A unit test never opens a socket to Redis or PostgreSQL, never starts the real application lifespan against those servers, and never starts Docker. `unittest.mock.patch` and `monkeypatch` are still forbidden. Logger, middleware, client, and config-model tests live in the shared packages.
