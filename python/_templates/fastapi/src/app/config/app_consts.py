"""Immutable protocol constants that must not be overridden by the environment.

Tenant and user headers, the docs paths, and the log ``app`` identity are a
contract with callers. They are not deployment settings: putting them in
``.env`` would invite a typo to break every request or Grafana filter.

Request-id headers live in ``shared_middlewares``. Probe and metrics paths live
in ``shared_config``.
"""

from typing import Final

APP_NAME: Final = "billing_api"
TENANT_ID_HEADER: Final = "X-Tenant-ID"
USER_ID_HEADER: Final = "X-User-ID"
SWAGGER_DOCS_ENDPOINT: Final = "/docs"
REDOC_ENDPOINT: Final = "/redoc"
FEATURE_FLAGS_LOGICAL_KEY: Final = "feature_flags"
