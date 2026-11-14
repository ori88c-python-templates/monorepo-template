# shared-middlewares

HTTP middleware used by both FastAPI and FastMCP apps. FastAPI-only headers live in `fastapi_middlewares`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)

## Belongs here

- `CorrelationIdMiddleware`, a raw ASGI wrapper. It prefers a non-empty `X-Request-ID`, then `X-Correlation-ID`, otherwise a UUID4. The chosen id is bound for the request with `structlog.contextvars`, stored on `scope["state"]`, and always returned as `X-Request-ID`.
- `make_unhandled_http_exception_handler`. Register it with `add_exception_handler(Exception, ...)`. It logs through the logger you pass in and returns a generic `500` body. The correlation id is read from request state because the contextvar is already unbound when Starlette calls the handler.
- The three names those two pieces share: `REQUEST_ID_HEADER`, `CORRELATION_ID_HEADER`, and `CORRELATION_ID_STATE_KEY`.

Callers import from `shared_middlewares`.

## Does not belong here

- Security headers. Those depend on the `secure` library and on documentation pages, so they live in `fastapi_middlewares`.
- FastAPI or FastMCP types. These middlewares are Starlette ASGI.
- Business logic, clients, or a global logger. Pass a child logger into the exception-handler factory.

## Exports

- `CorrelationIdMiddleware`
- `make_unhandled_http_exception_handler`
- `REQUEST_ID_HEADER` (`X-Request-ID`)
- `CORRELATION_ID_HEADER` (`X-Correlation-ID`)
- `CORRELATION_ID_STATE_KEY` (`correlation_id`)
