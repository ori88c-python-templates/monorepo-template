"""Wrapper around a redis-py async client with explicit lifecycle hooks."""

from typing import Final

from redis.asyncio import Redis
from structlog.typing import FilteringBoundLogger

from shared_config import RedisConfig, validate_app_name
from shared_redis.create_redis_key import create_redis_key


class RedisClient:
    """Owns one Redis connection pool for the process lifetime.

    Construction does not talk to the network: ``Redis.from_url`` is lazy. ``start``
    (and ``ping``) are what actually open a connection, which is why they run in the
    composition root's topological init rather than in ``__init__``.

    ``app_name`` is stored and prepended by every key helper via
    :func:`create_redis_key`. Callers pass the remaining segments only.
    ``get_string("feature_flag", tenant_id, name)`` cannot omit the app name.
    ``raw`` does not add the prefix. A key passed to ``raw`` is the caller's
    responsibility.

    Attributes:
        raw: The wrapped redis-py client, for commands that have no helper here.
    """

    def __init__(
        self,
        config: RedisConfig,
        logger: FilteringBoundLogger,
        app_name: str,
        *,
        client: Redis | None = None,
    ) -> None:
        """Build the wrapper. Does not connect.

        Args:
            config: Already-validated connection settings. The DSN is consumed here
                and never logged.
            logger: Child logger named after this class, injected by the composition
                root so this client does not build its own.
            app_name: App directory name. It must pass :func:`validate_app_name`.
                Every key helper prefixes it.
            client: Optional pre-built redis-py client. Production leaves this unset;
                tests pass a stand-in so nothing binds a real socket.

        Raises:
            ValueError: If ``app_name`` is not a lowercase identifier.
        """
        self._logger: Final = logger
        self._app_name: Final = validate_app_name(app_name)
        # redis-py types ``from_url`` with ``**kwargs: Unknown``, which leaks through
        # strict mode. The return is a ``Redis``; decode_responses makes values ``str``.
        self._client: Final[Redis] = (
            client
            if client is not None
            else Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
                str(config.DSN),
                decode_responses=True,
                socket_connect_timeout=config.CONNECT_TIMEOUT_SECONDS,
                socket_timeout=config.COMMAND_TIMEOUT_SECONDS,
                retry_on_timeout=False,
            )
        )

    @property
    def raw(self) -> Redis:
        """The wrapped redis-py client.

        Commands that have a method on this class should use that method.
        ``raw`` does not prefix ``app_name``. A key passed here is the caller's
        responsibility.

        Returns:
            The client constructed in ``__init__``. Responses are decoded to ``str``.
        """
        return self._client

    def _key(self, *parts: str) -> str:
        """Build a key that starts with this client's app name.

        Args:
            *parts: Segments after the app name.

        Returns:
            The encoded key.

        Raises:
            ValueError: If no parts were given.
        """
        return create_redis_key(self._app_name, *parts)

    async def start(self) -> None:
        """Open a connection by pinging the server.

        Raises:
            redis.exceptions.RedisError: If the server cannot be reached or PING
                fails. The composition root treats this as a failed startup.
        """
        self._logger.info("redis.starting")
        await self.ping()
        self._logger.info("redis.started")

    async def stop(self) -> None:
        """Close the connection pool.

        Safe to call if ``start`` never succeeded: redis-py closes an unused pool
        without requiring a prior connection.
        """
        self._logger.info("redis.stopping")
        await self._client.aclose()
        self._logger.info("redis.stopped")

    async def ping(self) -> None:
        """Confirm the existing pool can talk to Redis.

        Used by ``start`` and by the readiness probe. A failed ping raises; it does
        not return ``False``, so callers cannot ignore an unhealthy dependency.

        Raises:
            redis.exceptions.RedisError: If the command fails or the connection
                cannot be established.
            ConnectionError: If PING returns a value other than ``True``.
        """
        try:
            # redis-py types ``ping`` with ``**kwargs: Unknown``.
            pong = await self._client.ping()  # pyright: ignore[reportUnknownMemberType]
        except Exception:
            self._logger.exception("redis.ping.failed")
            raise
        if pong is not True:
            self._logger.error("redis.ping.unexpected_result", result=pong)
            raise ConnectionError("Redis PING did not return True.")

    async def get_string(self, *parts: str) -> str | None:
        """Return the string stored at the key built from ``parts``.

        Args:
            *parts: Segments after the app name.

        Returns:
            The stored string, or ``None`` when the key does not exist.
        """
        key = self._key(*parts)
        # redis-py types ``get`` with ``**kwargs: Unknown``. decode_responses
        # makes a present value a ``str``.
        value = await self._client.get(key)  # pyright: ignore[reportUnknownMemberType]
        if value is None:
            return None
        return value if isinstance(value, str) else str(value)

    async def set_string(self, *parts: str, value: str, ttl_seconds: int) -> None:
        """Store ``value`` at the key built from ``parts`` and expire it.

        Redis ``SET`` takes the expiry as whole seconds (``EX``). ``value`` and
        ``ttl_seconds`` are keyword-only so they are not taken as key parts.

        Args:
            *parts: Segments after the app name.
            value: String to store.
            ttl_seconds: How long the key lives, in seconds. Passed to Redis as ``EX``.
        """
        key = self._key(*parts)
        # redis-py types ``set`` with ``**kwargs: Unknown``.
        await self._client.set(key, value, ex=ttl_seconds)  # pyright: ignore[reportUnknownMemberType]

    async def append_list_item(self, *parts: str, item: str) -> None:
        """Append ``item`` to the tail of the list at the key built from ``parts``.

        A later ``read_list`` returns items in insertion order. The key is created
        when it does not exist. ``item`` is keyword-only so it is not a key part.

        Args:
            *parts: Segments after the app name.
            item: Value to append. Stored as a string.
        """
        key = self._key(*parts)
        # redis-py types ``rpush`` with ``**kwargs: Unknown``.
        await self._client.rpush(key, item)  # pyright: ignore[reportUnknownMemberType]

    async def read_list(self, *parts: str) -> list[str]:
        """Return every item in the list at the key built from ``parts``, oldest first.

        Args:
            *parts: Segments after the app name.

        Returns:
            The list, or an empty list when the key does not exist.
        """
        key = self._key(*parts)
        # redis-py types ``lrange`` with ``**kwargs: Unknown``. decode_responses
        # makes each element a ``str``.
        items = await self._client.lrange(key, 0, -1)  # pyright: ignore[reportUnknownMemberType]
        return [item if isinstance(item, str) else str(item) for item in items]
