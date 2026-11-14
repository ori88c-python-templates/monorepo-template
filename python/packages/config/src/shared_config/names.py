"""Names that become env segments or package directories."""

import re
from typing import Final

_IDENTIFIER: Final = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_app_name(app_name: str) -> str:
    """Return ``app_name`` when it can be an env prefix.

    The directory ``billing_api`` becomes the prefix ``BILLING_API``. Hyphens and
    uppercase letters are rejected so two directories cannot collapse to one prefix.

    Args:
        app_name: Directory name of a Python app.

    Returns:
        The same name.

    Raises:
        ValueError: If the name is not a lowercase identifier.
    """
    _require_identifier(app_name, kind="app name")
    return app_name


def validate_logical_database_key(logical_key: str) -> str:
    """Return ``logical_key`` when it can be a ``POSTGRES__<KEY>__`` segment.

    The key names the inventory entry and, later, ``python/packages/<key>_db``.
    It is not an app name and not the physical database name.

    Args:
        logical_key: Stable database identity, such as ``fruits``.

    Returns:
        The same key.

    Raises:
        ValueError: If the key is not a lowercase identifier.
    """
    _require_identifier(logical_key, kind="logical database key")
    return logical_key


def _require_identifier(value: str, *, kind: str) -> None:
    if _IDENTIFIER.fullmatch(value) is None:
        message = f"{kind} {value!r} must match {_IDENTIFIER.pattern}"
        raise ValueError(message)
