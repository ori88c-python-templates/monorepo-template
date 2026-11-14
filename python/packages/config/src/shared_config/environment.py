"""Deployment environment. One value for every process in this monorepo."""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model


class Environment(StrEnum):
    """The deployment environment the process is running in.

    ``LOCAL`` is a developer machine, as distinct from ``DEV``, which is a shared
    deployed environment.
    """

    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

    def include_probes_in_schema(self) -> bool:
        """Whether Kubernetes probe routes are part of the generated schema.

        Local and shared-dev include them so a developer-facing schema lists the
        probes. Staging and production omit them: kubelet is the only caller, and
        the paths are not product API. FastAPI reads this for OpenAPI. FastMCP
        reads it for the same route flag. ``GET /metrics`` is never included.

        Returns:
            True when this environment is ``local`` or ``dev``.
        """
        return self in (Environment.LOCAL, Environment.DEV)


class _EnvironmentFile(BaseModel):
    """The single ``ENV`` variable.

    This is not a nested ``ENVIRONMENT__ENV`` block. Both polyrepos use ``ENV``.
    """

    ENV: Environment = Environment.DEV


def load_environment(*, env_file: Path | UseRootEnv | None = USE_ROOT_ENV) -> Environment:
    """Load ``ENV``.

    Args:
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        The deployment environment. Unset means ``dev``.

    Raises:
        ValidationError: If ``ENV`` is not one of the four names.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_model(_EnvironmentFile, env_prefix="", env_file=env_file).ENV
