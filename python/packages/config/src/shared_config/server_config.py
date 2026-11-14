"""Bind address for one app process."""

from pathlib import Path

from pydantic import BaseModel, Field

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model
from shared_config.names import validate_app_name


class ServerConfig(BaseModel):
    """Bind address of one application's HTTP server.

    Several apps share one env file, so ``PORT`` has no default: a missing
    ``<APP>__SERVER__PORT`` fails at startup instead of colliding on 8080.

    Attributes:
        HOST: Interface to bind to. Defaults to ``0.0.0.0`` so the process is
            reachable from outside its container.
        PORT: TCP port to listen on. Required. Constrained to the valid port range.
    """

    # S104: binding to all interfaces is required, not accidental. A container's service has to
    # be reachable from outside its network namespace; exposure is controlled at the network layer.
    HOST: str = Field(default="0.0.0.0", min_length=1)  # noqa: S104
    PORT: int = Field(ge=1, le=65535)


def create_server_config(
    app_name: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> ServerConfig:
    """Load ``<APP>__SERVER__*``.

    Args:
        app_name: App directory name, such as ``billing_api``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated bind settings for that app.

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier.
        ValidationError: If ``PORT`` is missing or a value is invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    prefix = f"{validate_app_name(app_name).upper()}__SERVER__"
    return load_model(ServerConfig, env_prefix=prefix, env_file=env_file)
