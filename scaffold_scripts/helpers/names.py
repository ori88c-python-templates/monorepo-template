"""App names, categories, and the ports those names publish."""

import re
from dataclasses import dataclass
from typing import Final, NamedTuple

from shared_config import validate_app_name

from helpers.errors import ScaffoldError

FASTAPI: Final = "fastapi"
FASTMCP: Final = "fastmcp"
TASK_RUNNER: Final = "task_runner"
CATEGORIES: Final = frozenset({FASTAPI, FASTMCP, TASK_RUNNER})
MINIMUM_PORT: Final = 8081

_SYMBOL: Final = r"A-Za-z0-9_"
_ESCAPE_LETTERS: Final = "abfnrtv"
_SERVER_PORT: Final = re.compile(
    r"(?m)^(?!#)[^\n]*?([A-Z][A-Z0-9_]*)__SERVER__PORT[:=]\s*\"?(\d+)",
)
_CATEGORY: Final = re.compile(r'(?m)^type = "(fastapi|fastmcp|task_runner)"\s*$')


@dataclass(frozen=True)
class AppIdentity:
    """One installed app, in the spellings the repo uses for it.

    ``name`` is the directory and the import package. ``distribution_name``
    is the uv project and the Compose service. ``env_prefix`` is the
    ``<PREFIX>__`` segment. ``port`` is the published server port.
    ``None`` means this operation does not assign a port.
    """

    name: str
    category: str
    port: int | None

    @property
    def distribution_name(self) -> str:
        """Return the hyphenated project name."""
        return self.name.replace("_", "-")

    @property
    def env_prefix(self) -> str:
        """Return the uppercase env segment."""
        return self.name.upper()


def require_category(category: str) -> str:
    """Return ``category`` when it is a template this repo can copy.

    Raises:
        ScaffoldError: The category is not ``fastapi``, ``fastmcp``, or ``task_runner``.
    """
    if category not in CATEGORIES:
        message = f"Category must be fastapi, fastmcp, or task_runner. Got {category!r}."
        raise ScaffoldError(message)
    return category


def require_app_name(name: str) -> str:
    """Return ``name`` when it can be a directory and an env prefix.

    Raises:
        ScaffoldError: ``validate_app_name`` rejected the name.
    """
    try:
        return validate_app_name(name)
    except ValueError as exc:
        raise ScaffoldError(str(exc)) from exc


def category_from_pyproject(text: str) -> str:
    """Return the ``[tool.monorepo]`` type in an app ``pyproject.toml``.

    Raises:
        ScaffoldError: The table or the type value is missing.
    """
    section = re.search(r"(?ms)^\[tool\.monorepo\]\n(.*?)(?=^\[|\Z)", text)
    if section is None:
        message = "App pyproject.toml has no [tool.monorepo] type."
        raise ScaffoldError(message)
    match = _CATEGORY.search(section.group(1))
    if match is None:
        message = "App pyproject.toml has no [tool.monorepo] type."
        raise ScaffoldError(message)
    return match.group(1)


class ServerPort(NamedTuple):
    """One active server-port assignment."""

    env_prefix: str
    port: int


def server_ports(text: str) -> list[ServerPort]:
    """Return active ``<PREFIX>__SERVER__PORT`` assignments in ``text``.

    Commented lines are ignored. Compose uses ``PORT: "8081"`` and the env
    example uses ``PORT=8081``.
    """
    return [
        ServerPort(env_prefix=prefix, port=int(number))
        for prefix, number in _SERVER_PORT.findall(text)
    ]


def port_for_prefix(text: str, prefix: str) -> int | None:
    """Return the server port for ``prefix``, or ``None`` when it is absent."""
    for assignment in server_ports(text):
        if assignment.env_prefix == prefix:
            return assignment.port
    return None


def next_app_port(*texts: str) -> int:
    """Return the next published port.

    The value is one above the highest server port in ``texts``, and at
    least ``8081``.
    """
    ports = [assignment.port for text in texts for assignment in server_ports(text)]
    highest = max(ports, default=MINIMUM_PORT - 1)
    return max(highest, MINIMUM_PORT - 1) + 1


def identifier_boundary(extra: str = "") -> str:
    r"""Return the lookbehind that opens a whole-token match.

    A token starts where the previous character is not an identifier
    character. Inside a Python string literal, ``"\nGITHUB_REPORT__..."``
    puts the letter ``n`` right before the token, so a plain lookbehind
    would read the token as the tail of ``n``. The letter that closes a
    backslash escape is a boundary too.

    Args:
        extra: Characters that also count as identifier characters, such
            as ``-`` for a distribution name.

    Returns:
        A regex fragment with no capturing group.
    """
    return rf"(?:(?<![{_SYMBOL}{extra}])|(?<=\\[{_ESCAPE_LETTERS}]))"


def replace_symbol(text: str, old: str, new: str) -> str:
    """Replace ``old`` where it is a whole token, hyphens included."""
    if old in {new, ""}:
        return text
    pattern = re.compile(rf"{identifier_boundary('-')}{re.escape(old)}(?![{_SYMBOL}-])")
    return pattern.sub(lambda _match: new, text)


def replace_identity(text: str, source: AppIdentity, target: AppIdentity) -> str:
    """Replace ``source`` spellings with ``target`` spellings.

    The env prefix is replaced only as ``<PREFIX>__``. When the directory
    name and the distribution name are the same token, every occurrence
    becomes the new directory name. Callers then set distribution slots
    (project name, script, image command) explicitly.
    """
    prefix = re.compile(rf"{identifier_boundary()}{re.escape(source.env_prefix)}__")
    text = prefix.sub(f"{target.env_prefix}__", text)
    if source.distribution_name != source.name:
        text = replace_symbol(text, source.distribution_name, target.distribution_name)
    return replace_symbol(text, source.name, target.name)


def require_port(text: str, name: str) -> int:
    """Return the env-example port for ``name``.

    Raises:
        ScaffoldError: ``.env.example`` has no server port for the app.
    """
    prefix = name.upper()
    port = port_for_prefix(text, prefix)
    if port is None:
        message = f"App '{name}' has no {prefix}__SERVER__PORT in .env.example."
        raise ScaffoldError(message)
    return port
