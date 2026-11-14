"""Configuration for the shared PostgreSQL server and one chosen database."""

from pathlib import Path
from typing import Literal, Self
from urllib.parse import quote

from pydantic import BaseModel, Field, PostgresDsn, SecretStr, model_validator

from shared_config.loading import (
    USE_ROOT_ENV,
    UseRootEnv,
    fields_from_env,
    merged_environ,
    resolve_env_file,
)
from shared_config.names import validate_logical_database_key

SslMode = Literal["disable", "require", "verify-full"]

_BARE_DATABASE = "POSTGRES__DATABASE"


class PostgresConfig(BaseModel):
    """Connection settings for one physical PostgreSQL database.

    Host, credentials, and SSL are the shared server. ``DATABASE`` is the physical
    name chosen for one logical key via :func:`create_postgres_config`. Connect,
    statement, and pool-wait timeouts are explicit so a hung server or an exhausted
    pool cannot stall a worker. Pool sizing stays with SQLAlchemy's defaults.

    Attributes:
        HOST: Hostname or address of the database server.
        PORT: TCP port of the database server.
        DATABASE: Physical database name. Not read from ``POSTGRES__DATABASE``.
        USER: Role to authenticate as.
        PASSWORD: Password for the role, wrapped in :class:`~pydantic.SecretStr` so it
            is redacted in reprs and in ``model_dump()``.
        SSL_MODE: libpq SSL negotiation mode. ``verify-full`` is the only value that
            actually authenticates the server's certificate.
        CONNECT_TIMEOUT_SECONDS: Bound on opening the TCP connection (libpq
            ``connect_timeout``). Defaults to five. Values below one are rejected.
        STATEMENT_TIMEOUT_MS: Bound on a statement (PostgreSQL ``statement_timeout``).
            Defaults to five thousand. Values below one are rejected. Alembic does not
            use this field; slow DDL must not inherit it.
        POOL_TIMEOUT_SECONDS: How long SQLAlchemy waits for a free pooled connection
            (``pool_timeout``). Defaults to thirty, which is SQLAlchemy's own default,
            made visible. Values below one are rejected. Alembic uses ``NullPool`` and
            ignores this field.
    """

    HOST: str = Field(min_length=1)
    PORT: int = Field(default=5432, ge=1, le=65535)
    DATABASE: str = Field(min_length=1)
    USER: str = Field(min_length=1)
    PASSWORD: SecretStr
    SSL_MODE: SslMode = "require"
    CONNECT_TIMEOUT_SECONDS: int = Field(default=5, ge=1)
    STATEMENT_TIMEOUT_MS: int = Field(default=5000, ge=1)
    POOL_TIMEOUT_SECONDS: int = Field(default=30, ge=1)

    @model_validator(mode="after")
    def _validate_dsn_is_constructible(self) -> Self:
        """Fail fast if the individual settings do not compose into a valid URL.

        Without this the config would validate happily and only blow up later, at the
        point the engine is first created. Building the DSN here moves that failure to
        application startup.

        Returns:
            The validated model.

        Raises:
            ValueError: If the settings cannot be assembled into a valid PostgreSQL URL.
        """
        _ = self.DSN
        return self

    @property
    def DSN(self) -> PostgresDsn:
        """Assemble the PostgreSQL connection URL from the individual settings.

        This is a plain property rather than a ``computed_field`` on purpose: a
        computed field would be included in ``model_dump()`` and would therefore leak
        the password into anything that serialises the config, such as a log line.

        Credentials are percent-encoded first. ``PostgresDsn.build`` does not escape
        them, so a password containing ``@`` or ``/`` would silently produce a URL that
        parses into the wrong host or database.

        Returns:
            The connection URL, including credentials and the SSL mode query parameter.
            The scheme is ``postgresql+psycopg`` so SQLAlchemy's async engine uses
            psycopg3, which honours libpq ``sslmode``.
        """
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            host=self.HOST,
            port=self.PORT,
            path=self.DATABASE,
            username=quote(self.USER, safe=""),
            password=quote(self.PASSWORD.get_secret_value(), safe=""),
            query=f"sslmode={self.SSL_MODE}",
        )

    @property
    def connect_args(self) -> dict[str, int | str]:
        """DBAPI kwargs for the application engine.

        Not a ``computed_field`` so they are not serialised. Alembic must not pass this
        dict: ``statement_timeout`` would abort slow DDL.

        Returns:
            ``connect_timeout`` in seconds for libpq, and ``options`` setting PostgreSQL
            ``statement_timeout`` in milliseconds.
        """
        return {
            "connect_timeout": self.CONNECT_TIMEOUT_SECONDS,
            "options": f"-c statement_timeout={self.STATEMENT_TIMEOUT_MS}",
        }


def create_postgres_config(
    logical_key: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> PostgresConfig:
    """Load the shared Postgres server and one physical database name.

    ``logical_key`` selects ``POSTGRES__<KEY>__DATABASE``. Host, credentials, SSL,
    and timeouts come from the unprefixed ``POSTGRES__*`` block. Two callers that
    pass the same key share a database. One process may call this twice.

    Args:
        logical_key: Inventory key such as ``fruits``. Not an app name and not the
            physical database name.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated settings whose ``DATABASE`` is the physical name.

    Raises:
        ValueError: If the key is not an identifier, if ``POSTGRES__DATABASE`` is set,
            or if ``POSTGRES__<KEY>__DATABASE`` is missing or empty.
        ValidationError: If the server settings are missing or invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    logical_key = validate_logical_database_key(logical_key)
    resolved = resolve_env_file(env_file)
    values = merged_environ(resolved)
    if _BARE_DATABASE in values:
        message = (
            "POSTGRES__DATABASE is not used. Pass a logical database key to "
            "create_postgres_config; the physical name comes from "
            "POSTGRES__<KEY>__DATABASE."
        )
        raise ValueError(message)
    variable = f"POSTGRES__{logical_key.upper()}__DATABASE"
    physical = values.get(variable, "")
    if physical == "":
        message = (
            f"{variable} is required. It is the physical database name for logical key "
            f"{logical_key!r}."
        )
        raise ValueError(message)
    raw = fields_from_env(
        PostgresConfig,
        env_prefix="POSTGRES__",
        env_file=resolved,
        exclude=frozenset({"DATABASE"}),
    )
    raw["DATABASE"] = physical
    return PostgresConfig.model_validate(raw)
