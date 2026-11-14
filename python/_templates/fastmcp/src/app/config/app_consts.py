"""Immutable protocol constants that must not be overridden by the environment.

The log ``app`` identity and the MCP server name and instructions are a contract
with callers. They are not deployment settings: putting them in ``.env`` would
invite a typo to break a Grafana filter or a ``server/discover`` name.

Request-id headers live in ``shared_middlewares``. Probe and metrics paths live
in ``shared_config``.
"""

from typing import Final

APP_NAME: Final = "notes_mcp"
MCP_SERVER_NAME: Final = "Notes"
MCP_SERVER_INSTRUCTIONS: Final = "Redis-backed process with probes and Prometheus."
TENANT_ID_HEADER: Final = "X-Tenant-ID"
USER_ID_HEADER: Final = "X-User-ID"
