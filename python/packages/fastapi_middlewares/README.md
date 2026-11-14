# fastapi-middlewares

HTTP middleware that only FastAPI apps should depend on. A FastMCP app does not install this package, so it does not install `secure`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)

## Belongs here

- `SecureASGIMiddleware`, an adapter around the `secure` library. It applies the balanced header set on every HTTP response.
- `docs_path_prefixes`, defaulting to `/docs` and `/redoc`. On those paths, and on paths nested under them, the adapter drops only `Content-Security-Policy`, because Swagger UI and ReDoc load CDN scripts and an inline bootstrap that the balanced policy would block. Every other header still applies.
- An empty `docs_path_prefixes` keeps `Content-Security-Policy` on every response, including documentation pages.
- `default_secure_headers()`, which returns the library's balanced preset. Pass it as `secure=` when registering the middleware.

## Does not belong here

- Correlation ids and the unhandled-exception handler. Both apps use those, and they live in `shared_middlewares`.
- A dependency on `shared_middlewares`. This package does not call the other middlewares. The FastAPI app depends on both packages and registers them in its own composition root.

## Exports

- `SecureASGIMiddleware`
- `default_secure_headers`
