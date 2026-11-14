"""Cache TTL for feature-flag reads. The flag table lives in a database package."""

from pathlib import Path

from pydantic import BaseModel, Field

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model


class FeatureFlagConfig(BaseModel):
    """Settings for feature-flag reads and the Redis cache in front of them.

    Unprefixed: every app that uses flags shares one TTL. An app that has no flags
    does not call :func:`load_feature_flag_config`.

    Attributes:
        CACHE_TTL_SECONDS: How long a flag stays in Redis after a database load
            or a write. Defaults to three hundred (five minutes). Values below
            one are rejected because Redis ``SET EX`` takes an integer number of
            seconds, and zero would mean "no expiry".
    """

    CACHE_TTL_SECONDS: int = Field(default=300, ge=1)


def load_feature_flag_config(
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> FeatureFlagConfig:
    """Load ``FEATURE_FLAG__CACHE_TTL_SECONDS``.

    Args:
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated TTL settings. Unset means five minutes.

    Raises:
        ValidationError: If the TTL is below one second.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_model(FeatureFlagConfig, env_prefix="FEATURE_FLAG__", env_file=env_file)
