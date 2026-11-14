"""Insert and remove one app in the workspace ``pyproject.toml``."""

import re
from collections.abc import Callable
from typing import Final

from helpers.errors import ScaffoldError, already_exists_message
from helpers.names import AppIdentity

TEST_IGNORES: Final = '["S101", "S603", "PLR2004", "TRY301"]'
_OPENER_BY_ARRAY: Final = {
    "dependencies": "dependencies = [\n",
    "members": "members = [\n",
    "src": "src = [\n",
    "known_first_party": "known-first-party = [\n",
    "include": "include = [\n",
    "extra_paths": "extraPaths = [\n",
}


def add_workspace_app(text: str, identity: AppIdentity) -> str:
    """Register ``identity`` in the workspace file.

    Root pytest ``testpaths`` stay the shared packages. Pyright's global
    ``extraPaths`` gains the app ``src`` only. The execution environment
    adds the app directory as well, so each app's ``tests`` package stays
    separate.

    Raises:
        ScaffoldError: The app is already a workspace member.
    """
    if f'"apps/{identity.name}"' in text:
        raise ScaffoldError(already_exists_message(identity.name))
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["dependencies"],
        identity.distribution_name,
        _any_item,
    )
    text = insert_assignment(
        text,
        "[tool.uv.sources]\n",
        identity.distribution_name,
        f"{identity.distribution_name} = {{ workspace = true }}\n",
    )
    text = insert_array(text, _OPENER_BY_ARRAY["members"], f"apps/{identity.name}", _is_app_path)
    text = insert_array(text, _OPENER_BY_ARRAY["src"], f"apps/{identity.name}/src", _is_app_path)
    text = insert_array(text, _OPENER_BY_ARRAY["src"], f"apps/{identity.name}/tests", _is_app_path)
    text = insert_array(text, _OPENER_BY_ARRAY["known_first_party"], identity.name, _any_item)
    text = _insert_ignores(text, identity)
    text = insert_array(
        text, _OPENER_BY_ARRAY["include"], f"apps/{identity.name}/src", _is_app_path
    )
    text = insert_array(
        text, _OPENER_BY_ARRAY["include"], f"apps/{identity.name}/tests", _is_app_path
    )
    text = insert_array(
        text, _OPENER_BY_ARRAY["extra_paths"], f"apps/{identity.name}/src", _is_app_path
    )
    return _append_environment(text, identity)


def remove_workspace_app(text: str, identity: AppIdentity) -> str:
    """Drop ``identity`` from the workspace file.

    Missing lines are left missing. Deleting an app that was only partly
    registered still produces a coherent file.
    """
    lines = (
        f'    "{identity.distribution_name}",\n',
        f"{identity.distribution_name} = {{ workspace = true }}\n",
        f'    "apps/{identity.name}",\n',
        f'    "apps/{identity.name}/src",\n',
        f'    "apps/{identity.name}/tests",\n',
        f'    "{identity.name}",\n',
        f'"apps/{identity.name}/src/{identity.name}/config/*.py" = ["N802"]\n',
        f'"apps/{identity.name}/tests/**/*.py" = {TEST_IGNORES}\n',
    )
    for line in lines:
        text = text.replace(line, "")
    return _remove_environment(text, identity.name)


def rename_workspace_app(text: str, source: AppIdentity, target: AppIdentity) -> str:
    """Register ``target`` where ``source`` was registered."""
    return add_workspace_app(remove_workspace_app(text, source), target)


def _is_app_path(item: str) -> bool:
    return item.startswith("apps/")


def _any_item(_item: str) -> bool:
    return True


def insert_array(
    text: str,
    opener: str,
    item: str,
    belongs: Callable[[str], bool],
) -> str:
    """Insert ``item`` into the first array that opens with ``opener``.

    ``belongs`` decides which existing items share the sorted group. The item
    is placed among that group, before the first greater member.

    Raises:
        ScaffoldError: The array already contains ``item``.
    """
    start = text.index(opener) + len(opener)
    close = text.index("\n]", start)
    body = text[start:close]
    items = re.findall(r'"([^"]*)"', body)
    if item in items:
        message = f"Workspace list already contains {item!r}."
        raise ScaffoldError(message)
    updated = _insert_among(items, item, belongs)
    rendered = "\n".join(f'    "{value}",' for value in updated)
    return text[:start] + rendered + text[close:]


def _insert_among(items: list[str], new: str, belongs: Callable[[str], bool]) -> list[str]:
    insert_at: int | None = None
    last_belonging: int | None = None
    for index, item in enumerate(items):
        if not belongs(item):
            continue
        last_belonging = index
        if item > new:
            insert_at = index
            break
    if insert_at is not None:
        return [*items[:insert_at], new, *items[insert_at:]]
    if last_belonging is None:
        return [*items, new]
    return [*items[: last_belonging + 1], new, *items[last_belonging + 1 :]]


def insert_assignment(text: str, header: str, key: str, line: str) -> str:
    """Insert ``line`` into the table that starts at ``header``, sorted by key.

    Raises:
        ScaffoldError: ``key`` is already assigned in that table.
    """
    start = text.index(header) + len(header)
    next_header = re.search(r"(?m)^\[", text[start:])
    end = len(text) if next_header is None else start + next_header.start()
    body = text[start:end]
    if re.search(rf"(?m)^{re.escape(key)} =", body):
        message = f"Workspace sources already contain {key!r}."
        raise ScaffoldError(message)
    content = body.rstrip("\n")
    rows = content.split("\n") if content else []
    insert_at = len(rows)
    for index, row in enumerate(rows):
        if not row.strip():
            continue
        existing = row.split("=", 1)[0].strip()
        if existing > key:
            insert_at = index
            break
    rows.insert(insert_at, line.rstrip("\n"))
    rebuilt = "\n".join(rows) + "\n"
    if body.endswith("\n\n"):
        rebuilt += "\n"
    return text[:start] + rebuilt + text[end:]


def _insert_ignores(text: str, identity: AppIdentity) -> str:
    needle = "\n\n[tool.pyright]\n"
    if needle not in text:
        message = "Workspace pyproject.toml has no [tool.pyright] section."
        raise ScaffoldError(message)
    block = (
        f'"apps/{identity.name}/src/{identity.name}/config/*.py" = ["N802"]\n'
        f'"apps/{identity.name}/tests/**/*.py" = {TEST_IGNORES}\n'
    )
    return text.replace(needle, "\n" + block + "\n[tool.pyright]\n", 1)


def _append_environment(text: str, identity: AppIdentity) -> str:
    if not text.endswith("\n"):
        text += "\n"
    return (
        text
        + "\n"
        + "[[tool.pyright.executionEnvironments]]\n"
        + f'root = "apps/{identity.name}"\n'
        + f'extraPaths = ["apps/{identity.name}", "apps/{identity.name}/src"]\n'
    )


def _remove_environment(text: str, name: str) -> str:
    pattern = re.compile(
        "\n"
        r"\[\[tool\.pyright\.executionEnvironments\]\]\n"
        rf'root = "apps/{re.escape(name)}"\n'
        rf'extraPaths = \["apps/{re.escape(name)}", "apps/{re.escape(name)}/src"\]\n',
    )
    return pattern.sub("", text, count=1)
