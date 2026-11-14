"""Workspace members and the depends-on edges between them."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, TypeGuard

from helpers.errors import SelectionError
from helpers.toml_tables import object_dict, object_list, requirement_groups, requirement_strings

_NAME: Final = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
MemberKind = Literal["package", "app"]


@dataclass(frozen=True)
class Member:
    """One workspace member read from its ``pyproject.toml``.

    ``path`` is the workspace path, such as ``packages/config``. ``name`` is the
    directory name and the graph node id. ``distribution`` is ``project.name``.
    ``table`` is the parsed project file.
    """

    path: str
    kind: MemberKind
    name: str
    distribution: str
    table: Mapping[str, object]


@dataclass(frozen=True)
class WorkspaceGraph:
    """Packages, apps, and which workspace member depends on which.

    ``dependency_names_by_member`` maps every node to the workspace nodes it
    depends on. A third-party requirement is not a node. The map cannot be mutated.
    """

    packages: frozenset[str]
    apps: frozenset[str]
    dependency_names_by_member: Mapping[str, frozenset[str]]


def load_graph(python_dir: Path) -> WorkspaceGraph:
    """Read the uv workspace rooted at ``python_dir``.

    Each ``[tool.uv.workspace] members`` entry becomes one node. The node id
    is the directory name, not the distribution name. An edge exists when a
    member's dependencies, optional-dependencies, or dependency-groups name
    another member. Third-party pins are ignored.

    Args:
        python_dir: Directory that contains the workspace ``pyproject.toml``.

    Returns:
        The packages, the apps, and the depends-on edges.

    Raises:
        SelectionError: The workspace file or a member cannot be read.
    """
    root = _load_toml(python_dir / "pyproject.toml")
    members = [read_member(python_dir, path) for path in _member_paths(root)]
    _reject_duplicate_names(members)
    member_name_by_distribution = _distribution_index(members)
    dependency_names_by_member = {
        member.name: _workspace_dependencies(member, member_name_by_distribution)
        for member in members
    }
    return WorkspaceGraph(
        packages=frozenset(member.name for member in members if member.kind == "package"),
        apps=frozenset(member.name for member in members if member.kind == "app"),
        dependency_names_by_member=MappingProxyType(dependency_names_by_member),
    )


def read_member(python_dir: Path, member: str) -> Member:
    """Read one workspace member from ``python_dir / member``.

    ``member`` is a workspace path such as ``packages/config`` or
    ``apps/billing_api``. The distribution is that file's ``project.name``.

    Args:
        python_dir: Directory that contains the workspace ``pyproject.toml``.
        member: A path relative to ``python_dir``.

    Returns:
        The member's kind, directory name, distribution name, and parsed table.

    Raises:
        SelectionError: The path is not ``packages/<name>`` or ``apps/<name>``,
            or the file has no ``project.name``.
    """
    prefix, separator, name = member.partition("/")
    kind = _kind(prefix)
    if separator != "/" or kind is None or not name or "/" in name:
        raise SelectionError(f"Workspace member '{member}' is not packages/<name> or apps/<name>.")
    table = _load_toml(python_dir / member / "pyproject.toml")
    project = _project(table, member)
    distribution = project.get("name")
    if not isinstance(distribution, str) or not distribution.strip():
        raise SelectionError(f"{member} has no project.name.")
    return Member(
        path=member,
        kind=kind,
        name=name,
        distribution=distribution,
        table=table,
    )


def requirement_name(requirement: object) -> str:
    """Return the normalized distribution name from a PEP 508 requirement.

    Args:
        requirement: One dependency string, extras and version spec included.

    Returns:
        The name, lowercased, with ``_`` and ``.`` treated as ``-``.

    Raises:
        SelectionError: ``requirement`` is not a string or has no name.
    """
    if not isinstance(requirement, str):
        raise SelectionError("A dependency is not a string.")
    text = requirement.split(";", 1)[0].strip().split("[", 1)[0].strip()
    match = _NAME.match(text)
    if match is None:
        raise SelectionError(f"Cannot read a distribution name from {requirement!r}.")
    return normalize_distribution(match.group(0))


def normalize_distribution(name: str) -> str:
    """Return the packaging-normalized form of a distribution name.

    Args:
        name: A ``project.name`` or a requirement name.

    Returns:
        Lowercase, with runs of ``-``, ``_``, and ``.`` collapsed to ``-``.
    """
    return re.sub(r"[-_.]+", "-", name).strip("-").lower()


def _reject_duplicate_names(members: Sequence[Member]) -> None:
    seen: set[str] = set()
    for member in members:
        if member.name in seen:
            message = f"Two workspace members use the directory name '{member.name}'."
            raise SelectionError(message)
        seen.add(member.name)


def _distribution_index(members: Sequence[Member]) -> Mapping[str, str]:
    """Map a normalized distribution name to the member directory."""
    member_name_by_distribution: dict[str, str] = {}
    for member in members:
        key = normalize_distribution(member.distribution)
        if key in member_name_by_distribution:
            message = f"Two workspace members use the distribution name '{member.distribution}'."
            raise SelectionError(message)
        member_name_by_distribution[key] = member.name
    return member_name_by_distribution


def _workspace_dependencies(
    member: Member,
    member_name_by_distribution: Mapping[str, str],
) -> frozenset[str]:
    """Return the other workspace members this member depends on.

    Third-party requirements are ignored. A member does not depend on itself.
    """
    targets: set[str] = set()
    for requirement in _requirement_names(member.table):
        owner = member_name_by_distribution.get(requirement_name(requirement))
        if owner is not None and owner != member.name:
            targets.add(owner)
    return frozenset(targets)


def _requirement_names(table: Mapping[str, object]) -> tuple[str, ...]:
    project = object_dict(table.get("project")) or {}
    strings = list(requirement_strings(project.get("dependencies")))
    strings.extend(_group_strings(project.get("optional-dependencies")))
    strings.extend(_group_strings(table.get("dependency-groups")))
    return tuple(strings)


def _group_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    for group in requirement_groups(value):
        strings.extend(group.requirements)
    return tuple(strings)


def _kind(prefix: str) -> MemberKind | None:
    if prefix == "packages":
        return "package"
    if prefix == "apps":
        return "app"
    return None


def _member_paths(root: Mapping[str, object]) -> Sequence[str]:
    tool = object_dict(root.get("tool")) or {}
    uv = object_dict(tool.get("uv")) or {}
    workspace = object_dict(uv.get("workspace")) or {}
    members = workspace.get("members")
    if not _is_path_list(members):
        raise SelectionError("tool.uv.workspace.members must be a list of paths.")
    return members


def _is_path_list(members: object) -> TypeGuard[list[str]]:
    items = object_list(members)
    if items is None or not items:
        return False
    return all(isinstance(item, str) for item in items)


def _load_toml(path: Path) -> Mapping[str, object]:
    if not path.is_file():
        raise SelectionError(f"Missing {path.as_posix()}.")
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SelectionError(f"{path.as_posix()} is not valid TOML.") from exc
    table = object_dict(loaded)
    if table is None:
        raise SelectionError(f"{path.as_posix()} is not a table.")
    return table


def _project(parsed: Mapping[str, object], member: str) -> Mapping[str, object]:
    project = object_dict(parsed.get("project"))
    if project is None:
        raise SelectionError(f"{member} has no project table.")
    return project
