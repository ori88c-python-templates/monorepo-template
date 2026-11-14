"""Alembic environment for the feature_flags database.

This process is not an application. It builds a synchronous engine from
``create_postgres_config("feature_flags")`` and ``PostgresBase.metadata``.
It does not construct ``PostgresClient`` and does not require Redis settings.

``NullPool`` so the process does not hold a pool after it exits.
``connect_timeout`` comes from ``POSTGRES__CONNECT_TIMEOUT_SECONDS``. Statement
timeout is omitted so slow DDL is not killed by the application's statement bound.
"""

from logging.config import fileConfig
from typing import Final

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from feature_flags_db.constants import LOGICAL_KEY
from feature_flags_db.feature_flag_row import FeatureFlagRow
from feature_flags_db.postgres_base import PostgresBase
from shared_config import PostgresConfig, create_postgres_config

# Importing the row class registers it on PostgresBase.metadata for autogenerate.
_ORM_TABLES: Final = (FeatureFlagRow,)
_ = _ORM_TABLES

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PostgresBase.metadata


def postgres_settings() -> PostgresConfig:
    """Load the feature_flags database settings.

    Returns:
        Validated PostgreSQL settings, including connect timeout. The DSN is
        never logged.
    """
    return create_postgres_config(LOGICAL_KEY)


def run_migrations_offline() -> None:
    """Emit SQL to stdout without opening a database connection.

    Uses the DSN from the environment, not the placeholder in ``alembic.ini``.
    """
    context.configure(
        url=str(postgres_settings().DSN),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure the Alembic context on a connection Alembic can drive.

    Args:
        connection: Sync connection from the migration-owned engine.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database on a migration-owned sync engine."""
    postgres = postgres_settings()
    connectable = create_engine(
        str(postgres.DSN),
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": postgres.CONNECT_TIMEOUT_SECONDS,
        },
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
