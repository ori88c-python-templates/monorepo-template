"""Header names and the request-state key used by the shared HTTP middleware.

Tenant and user headers and the MCP server identity stay in each app. Probe and
metrics paths live in ``shared_config``.
"""

from typing import Final

REQUEST_ID_HEADER: Final = "X-Request-ID"
CORRELATION_ID_HEADER: Final = "X-Correlation-ID"
CORRELATION_ID_STATE_KEY: Final = "correlation_id"
