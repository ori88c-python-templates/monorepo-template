"""Insert and remove one package in the workspace ``pyproject.toml``."""

import re
from collections.abc import Callable
from typing import Final

from helpers.errors import ScaffoldError
from helpers.package_names import PackageIdentity
from helpers.workspace_toml import TEST_IGNORES, insert_array, insert_assignment

_OPENER_BY_ARRAY: Final = {
    "dependencies": "dependencies = [\n",
    "members": "members = [\n",
    "testpaths": "testpaths = [\n",
    "src": "src = [\n",
    "known_first_party": "known-first-party = [\n",
    "include": "include = [\n",
    "extra_paths": "extraPaths = [\n",
}
_IGNORES_HEADER: Final = "[tool.ruff.lint.per-file-ignores]\n"
_SOURCES_HEADER: Final = "[tool.uv.sources]\n"


def add_workspace_package(text: str, identity: PackageIdentity) -> str:
    """Register ``identity`` in the workspace file.

    Pyright ``extraPaths`` gains the package ``src`` only. Packages do not
    get an execution environment. Pytest ``testpaths`` gains the package tests.

    Raises:
        ScaffoldError: A list already contains one of the new entries, or the
            ignore section is missing.
    """
    text = insert_array(
        text, _OPENER_BY_ARRAY["dependencies"], identity.distribution_name, _any_item
    )
    text = insert_assignment(
        text,
        _SOURCES_HEADER,
        identity.distribution_name,
        f"{identity.distribution_name} = {{ workspace = true }}\n",
    )
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["members"],
        f"packages/{identity.directory}",
        _is_package_path,
    )
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["testpaths"],
        f"packages/{identity.directory}/tests",
        _is_package_path,
    )
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["src"],
        f"packages/{identity.directory}/src",
        _is_package_path,
    )
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["src"],
        f"packages/{identity.directory}/tests",
        _is_package_path,
    )
    text = insert_array(
        text, _OPENER_BY_ARRAY["known_first_party"], identity.import_name, _any_item
    )
    text = _insert_ignore(text, identity.directory)
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["include"],
        f"packages/{identity.directory}/src",
        _is_package_path,
    )
    text = insert_array(
        text,
        _OPENER_BY_ARRAY["include"],
        f"packages/{identity.directory}/tests",
        _is_package_path,
    )
    return insert_array(
        text,
        _OPENER_BY_ARRAY["extra_paths"],
        f"packages/{identity.directory}/src",
        _is_package_path,
    )


def remove_workspace_package(text: str, identity: PackageIdentity) -> str:
    """Drop ``identity`` and any extra paths under its directory.

    An Alembic path, a one-line ``pythonpath`` entry, an extra ignore, and a
    pyright execution environment rooted in the package are removed too.
    Missing entries are left missing.
    """
    drop_path = _under_package(identity.directory)
    text = _drop_items(text, _OPENER_BY_ARRAY["dependencies"], _equals(identity.distribution_name))
    text = text.replace(f"{identity.distribution_name} = {{ workspace = true }}\n", "")
    for opener in (
        _OPENER_BY_ARRAY["members"],
        _OPENER_BY_ARRAY["testpaths"],
        _OPENER_BY_ARRAY["src"],
        _OPENER_BY_ARRAY["include"],
        _OPENER_BY_ARRAY["extra_paths"],
    ):
        text = _drop_items(text, opener, drop_path)
    text = _drop_items(text, _OPENER_BY_ARRAY["known_first_party"], _equals(identity.import_name))
    text = _drop_ignore_lines(text, identity.directory)
    text = _drop_inline_array(text, "pythonpath", drop_path)
    return _drop_environments(text, identity.directory)


def _is_package_path(item: str) -> bool:
    return item.startswith("packages/")


def _any_item(_item: str) -> bool:
    return True


def _equals(expected: str) -> Callable[[str], bool]:
    def matches(item: str) -> bool:
        return item == expected

    return matches


def _under_package(directory: str) -> Callable[[str], bool]:
    prefix = f"packages/{directory}"

    def matches(item: str) -> bool:
        return item == prefix or item.startswith(f"{prefix}/")

    return matches


def _insert_ignore(text: str, directory: str) -> str:
    key = f"packages/{directory}/tests/**/*.py"
    line = f'"{key}" = {TEST_IGNORES}\n'
    if _IGNORES_HEADER not in text:
        message = "Workspace pyproject.toml has no [tool.ruff.lint.per-file-ignores] section."
        raise ScaffoldError(message)
    start = text.index(_IGNORES_HEADER) + len(_IGNORES_HEADER)
    next_header = re.search(r"(?m)^\[", text[start:])
    end = len(text) if next_header is None else start + next_header.start()
    rows = text[start:end].splitlines(keepends=True)
    rows.insert(_ignore_index(rows, key), line)
    return text[:start] + "".join(rows) + text[end:]


def _ignore_index(rows: list[str], key: str) -> int:
    insert_at = len(rows)
    last_package: int | None = None
    for index, row in enumerate(rows):
        match = re.match(r'^"([^"]+)"', row)
        if match is None or not match.group(1).startswith("packages/"):
            continue
        last_package = index
        if match.group(1) > key:
            return index
    if last_package is not None:
        return last_package + 1
    return insert_at


def _drop_items(text: str, opener: str, drop: Callable[[str], bool]) -> str:
    start_at = text.find(opener)
    if start_at == -1:
        return text
    start = start_at + len(opener)
    close = text.find("\n]", start)
    if close == -1:
        return text
    items = re.findall(r'"([^"]*)"', text[start:close])
    kept = [item for item in items if not drop(item)]
    if len(kept) == len(items):
        return text
    rendered = "\n".join(f'    "{value}",' for value in kept)
    return text[:start] + rendered + text[close:]


def _drop_ignore_lines(text: str, directory: str) -> str:
    pattern = re.compile(rf'^"packages/{re.escape(directory)}(?:/|")')
    kept = [line for line in text.splitlines(keepends=True) if pattern.match(line) is None]
    return "".join(kept)


def _drop_inline_array(text: str, key: str, drop: Callable[[str], bool]) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)} = \[(.*)\]\n")

    def replace(match: re.Match[str]) -> str:
        items = re.findall(r'"([^"]*)"', match.group(1))
        kept = [item for item in items if not drop(item)]
        if len(kept) == len(items):
            return match.group(0)
        if not kept:
            return ""
        inner = ", ".join(f'"{value}"' for value in kept)
        return f"{key} = [{inner}]\n"

    return pattern.sub(replace, text)


def _drop_environments(text: str, directory: str) -> str:
    prefix = f"packages/{directory}"
    pattern = re.compile(
        r"\n\[\[tool\.pyright\.executionEnvironments\]\]\n(?P<body>.*?)(?=\n\[\[|\Z)",
        re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        root = re.search(r'(?m)^root = "([^"]+)"', match.group("body"))
        if root is None:
            return match.group(0)
        value = root.group(1)
        if value == prefix or value.startswith(f"{prefix}/"):
            return ""
        return match.group(0)

    return pattern.sub(replace, text)
