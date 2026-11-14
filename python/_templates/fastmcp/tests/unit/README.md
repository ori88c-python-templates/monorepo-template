# unit

In-process tests only.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)

## Belongs here

Dependencies are passed in. The log manager comes from `shared_log_manager.testing`. Redis comes from `tests/unit/conftest.py`.

Layout mirrors the app package: one directory per area, then one directory per component, then one file per feature.

```
http_routes/        register_k8s_probes, get_http_route_logger
mcp_primitives/     get_user_details
registrator_funcs/  registration calls stay in register_*.py
prometheus/         metrics route is omitted from schema and still served
services/           user_notes_service
distribution/       this checkout reports an installed version
```

`tests/unit/conftest.py` owns `redis_client`. Probe tests set `ping.side_effect` on that fixture. Service unit tests use the same mock and a private Prometheus registry.

## Does not belong here

A unit test never opens a socket to Redis, never starts the real application lifespan against that server, and never starts Docker. `unittest.mock.patch` and `monkeypatch` are still forbidden. Logger, middleware, client, and config-model tests live in the shared packages.
