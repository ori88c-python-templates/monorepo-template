"""Run Alembic ``upgrade head`` against the session's throwaway PostgreSQL.

``feature_flags_db`` ``env.py`` calls ``create_postgres_config("feature_flags")``.
This module points env vars at the Testcontainers database for the upgrade,
then restores the process environment. Redis is not required.
"""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from alembic import command
from alembic.config import Config

from tests.throwaway_stores import ThrowawayStores

_ALEMBIC_INI: Final = (
    Path(__file__).resolve().parents[3] / "packages" / "feature_flags_db" / "alembic.ini"
)
_ALEMBIC_ENV_KEYS: Final = (
    "POSTGRES__HOST",
    "POSTGRES__PORT",
    "POSTGRES__FEATURE_FLAGS__DATABASE",
    "POSTGRES__USER",
    "POSTGRES__PASSWORD",
    "POSTGRES__SSL_MODE",
    "POSTGRES__DATABASE",
)


def upgrade_to_head(stores: ThrowawayStores) -> None:
    """Apply migrations and restore the process environment.

    Args:
        stores: Connection settings derived from the running containers.
    """
    env_value_by_key = _snapshot_env(_ALEMBIC_ENV_KEYS)
    try:
        _apply_alembic_env(stores)
        command.upgrade(Config(str(_ALEMBIC_INI)), "head")
    finally:
        _restore_env(env_value_by_key)


def _apply_alembic_env(stores: ThrowawayStores) -> None:
    """Point Alembic at the throwaway Postgres database.

    Args:
        stores: Connection settings derived from the running containers.
    """
    os.environ.update(
        {
            "POSTGRES__HOST": stores.postgres.HOST,
            "POSTGRES__PORT": str(stores.postgres.PORT),
            "POSTGRES__FEATURE_FLAGS__DATABASE": stores.postgres.DATABASE,
            "POSTGRES__USER": stores.postgres.USER,
            "POSTGRES__PASSWORD": stores.postgres.PASSWORD.get_secret_value(),
            "POSTGRES__SSL_MODE": stores.postgres.SSL_MODE,
        }
    )
    os.environ.pop("POSTGRES__DATABASE", None)


def _snapshot_env(keys: tuple[str, ...]) -> dict[str, str | None]:
    """Capture the process environment for the keys Alembic might change.

    Args:
        keys: Names to restore after the upgrade.

    Returns:
        Current values, or ``None`` when a key is unset.
    """
    env_value_by_key = {key: os.environ.get(key) for key in keys}
    return env_value_by_key  # noqa: RET504


def _restore_env(env_value_by_key: Mapping[str, str | None]) -> None:
    """Put the process environment back.

    Args:
        env_value_by_key: Value captured for each env key before the upgrade.
    """
    for key, value in env_value_by_key.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
