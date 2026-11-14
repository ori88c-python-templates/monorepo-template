"""Streamable HTTP settings for one FastMCP app."""

from pathlib import Path
from typing import Final, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from shared_config.infrastructure_paths import LIVEZ_ENDPOINT, METRICS_ENDPOINT, READYZ_ENDPOINT
from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model
from shared_config.names import validate_app_name

_INFRASTRUCTURE_PATHS: Final = frozenset({LIVEZ_ENDPOINT, READYZ_ENDPOINT, METRICS_ENDPOINT})


class McpConfig(BaseModel):
    """Path and response shape of one app's stateless MCP endpoint.

    The server name, instructions, and stateless HTTP mode stay constants in the
    app. Putting them in ``.env`` would let a typo rename the server clients
    discover. Each app has its own ``<APP>__MCP__*`` block.

    Attributes:
        PATH: Path of the streamable HTTP endpoint. Defaults to ``/mcp``.
        ENABLE_SSE_STREAM_RESPONSE: When true, one stateless request may stream
            progress as server-sent events. When false, that request returns a
            single JSON body. Defaults to true so a tool can report progress.
    """

    PATH: str = Field(default="/mcp", min_length=1)
    ENABLE_SSE_STREAM_RESPONSE: bool = True

    @field_validator("PATH")
    @classmethod
    def _path_is_absolute(cls, value: str) -> str:
        """Require a URL path, not a host or a query string.

        Args:
            value: The configured MCP endpoint path.

        Returns:
            The same path when it is absolute and has no query or fragment.

        Raises:
            ValueError: If the path is not a single absolute URL path.
        """
        if not value.startswith("/") or "?" in value or "#" in value:
            message = "PATH must be an absolute path without a query or fragment."
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _path_is_not_an_infrastructure_route(self) -> Self:
        """Keep the MCP endpoint off the probe and scrape paths.

        Returns:
            This config when ``PATH`` does not collide with kubelet or Prometheus.

        Raises:
            ValueError: If ``PATH`` is ``/livez``, ``/readyz``, or ``/metrics``.
        """
        if self.PATH in _INFRASTRUCTURE_PATHS:
            message = "PATH must not reuse a probe or metrics path."
            raise ValueError(message)
        return self


def create_mcp_config(
    app_name: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> McpConfig:
    """Load ``<APP>__MCP__*``.

    Args:
        app_name: App directory name, such as ``billing_api``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated MCP settings. Unset fields keep ``/mcp`` and SSE enabled.

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier.
        ValidationError: If ``PATH`` is not an absolute product path.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    prefix = f"{validate_app_name(app_name).upper()}__MCP__"
    return load_model(McpConfig, env_prefix=prefix, env_file=env_file)
