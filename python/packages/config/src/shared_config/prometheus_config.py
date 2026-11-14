"""Configuration for the Prometheus scrape endpoint."""

from pathlib import Path

from pydantic import BaseModel

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model


class PrometheusConfig(BaseModel):
    """Settings for ``GET /metrics``.

    The scrape path is not a field on this model. ``METRICS_ENDPOINT``,
    ``LIVEZ_ENDPOINT``, and ``READYZ_ENDPOINT`` live in ``infrastructure_paths``
    so a ``.env`` typo cannot rename them. Schema inclusion is not here either:
    the scrape path is never marked ``include_in_schema``. The gzip flag is
    unprefixed because every app in one deployment uses the same choice.

    Attributes:
        SHOULD_GZIP: Whether to gzip when the client sends ``Accept-Encoding``.
            Defaults to ``False``: the library prefers CPU over extra bandwidth.
    """

    SHOULD_GZIP: bool = False


def load_prometheus_config(
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> PrometheusConfig:
    """Load ``PROMETHEUS__SHOULD_GZIP``.

    Args:
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated scrape settings. Unset means gzip stays off.

    Raises:
        ValidationError: If the value is not a boolean.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_model(PrometheusConfig, env_prefix="PROMETHEUS__", env_file=env_file)
