"""Build ``AppConfig`` from an explicit env file, not the working directory."""

from pathlib import Path

from app.config import AppConfig
from app.config import load_app_config as _load_app_config


def load_app_config(env_file: Path | None = None) -> AppConfig:
    """Load configuration from the process environment and ``env_file`` only.

    A developer's repo-root ``.env`` must neither change what a test sees nor fail it
    when the test passes a file. Pass ``None`` to read no file at all. The process
    environment still applies, exactly as in production.

    Args:
        env_file: Dotenv file to read, or ``None`` to read none at all.

    Returns:
        The validated configuration.
    """
    return _load_app_config(env_file=env_file)
