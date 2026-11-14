"""Configuration for the Redis connection shared by every app."""

from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, Field, RedisDsn, SecretStr

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_model


class RedisConfig(BaseModel):
    """Connection settings for a single Redis instance.

    Host and credentials vary per deployment. Timeouts are explicit so a hung
    socket cannot stall a worker; encoding and the rest of redis-py's defaults
    stay with the client. Every app reads the same ``REDIS__*`` block. Key
    namespacing is a later client concern, not a field here.

    Attributes:
        HOST: Hostname or address of the Redis server.
        PORT: TCP port of the Redis server.
        DB: Logical database index to select after connecting.
        PASSWORD: Password for the connection, or ``None`` for an unauthenticated
            server. Wrapped in :class:`~pydantic.SecretStr` so it is redacted in
            reprs and in ``model_dump()``.
        USE_TLS: Whether to connect over TLS, which selects the ``rediss`` scheme.
        CONNECT_TIMEOUT_SECONDS: Bound on opening the TCP connection
            (``socket_connect_timeout``). Defaults to five. Values below one are
            rejected.
        COMMAND_TIMEOUT_SECONDS: Bound on a Redis command (``socket_timeout``).
            Defaults to five. Values below one are rejected.
    """

    HOST: str = Field(min_length=1)
    PORT: int = Field(default=6379, ge=1, le=65535)
    DB: int = Field(default=0, ge=0)
    PASSWORD: SecretStr | None = None
    USE_TLS: bool = False
    CONNECT_TIMEOUT_SECONDS: int = Field(default=5, ge=1)
    COMMAND_TIMEOUT_SECONDS: int = Field(default=5, ge=1)

    @property
    def DSN(self) -> RedisDsn:
        """Assemble the Redis connection URL from the individual settings.

        This is a plain property rather than a ``computed_field`` on purpose: a
        computed field would be included in ``model_dump()`` and would therefore leak
        the password into anything that serialises the config, such as a log line.

        The password is percent-encoded first. ``RedisDsn.build`` does not escape it, so
        a password containing ``@`` or ``/`` would silently produce a URL that parses
        into the wrong host or database index.

        Returns:
            The connection URL, including credentials when a password is configured.
        """
        password = self.PASSWORD.get_secret_value() if self.PASSWORD else None
        return RedisDsn.build(
            scheme="rediss" if self.USE_TLS else "redis",
            host=self.HOST,
            port=self.PORT,
            path=str(self.DB),
            password=quote(password, safe="") if password else None,
        )


def load_redis_config(*, env_file: Path | UseRootEnv | None = USE_ROOT_ENV) -> RedisConfig:
    """Load ``REDIS__*`` from the process environment and an env file.

    Args:
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated Redis settings.

    Raises:
        ValidationError: If a required setting is missing or a value is invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_model(RedisConfig, env_prefix="REDIS__", env_file=env_file)
