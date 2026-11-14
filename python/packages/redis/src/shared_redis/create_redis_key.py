"""Build a Redis key whose parts cannot collide across a colon."""


def create_redis_key(prefix: str, *parts: str) -> str:
    """Build a Redis key from ``prefix`` and ``parts``.

    Each part is written as ``len(part):part``. The pieces are joined with
    ``:``. The length keeps a colon inside a part from merging with the next
    part. ``create_redis_key("billing_api", "feature_flag", "a", "b:c")`` is
    ``billing_api:12:feature_flag:1:a:3:b:c``.

    ``RedisClient`` passes the app name as ``prefix``. Callers of this function
    directly must do the same.

    Args:
        prefix: Leading namespace. It is not length-prefixed. For app data this
            is the app directory name.
        *parts: Key segments. A caller converts a non-string before the call.

    Returns:
        The joined key.

    Raises:
        ValueError: If ``prefix`` is empty or no parts were given.
    """
    if not prefix:
        raise ValueError("A Redis key needs a non-empty prefix.")
    if not parts:
        raise ValueError("A Redis key needs at least one part after the prefix.")
    pieces = [prefix]
    for part in parts:
        pieces.append(str(len(part)))
        pieces.append(part)
    return ":".join(pieces)
