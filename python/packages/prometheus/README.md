# shared-prometheus

Scrape setup for any Starlette app, including FastAPI and FastMCP. Probe route functions stay in the app.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)

## Belongs here

- `PrometheusManager`. It installs default HTTP metrics, wraps the app with middleware, and mounts `GET /metrics`. `add_middleware` and `add_metrics_router` take a `Starlette` app.
- `make_inbound_request_id_instrumentation`, a sample HTTP callback that counts requests arriving with `X-Request-ID`. Register it with `add_http_instrumentation` before `add_middleware`.
- Default HTTP series exclude `LIVEZ_ENDPOINT`, `READYZ_ENDPOINT`, and `METRICS_ENDPOINT`, imported from `shared_config`. The scrape router mounts `METRICS_ENDPOINT`.

## Does not belong here

- The probe route handlers. Each app registers `/livez` and `/readyz`.
- The path constants. `LIVEZ_ENDPOINT`, `READYZ_ENDPOINT`, and `METRICS_ENDPOINT` are `shared_config`.
- Product counters that a service increments. Those stay next to the service, in the app.
- A FastAPI-only dependency beyond what `prometheus-fastapi-instrumentator` already requires. Both templates already use that library.

## Exports

Import from `shared_prometheus`:

- `PrometheusManager`
- `make_inbound_request_id_instrumentation`
