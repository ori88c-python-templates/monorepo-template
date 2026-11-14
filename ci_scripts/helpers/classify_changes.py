"""Map changed paths to the packages and apps that must be tested."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal

from helpers.dependents import affected_nodes
from helpers.errors import SelectionError
from helpers.toml_tables import (
    RequirementGroup,
    object_dict,
    requirement_groups,
    requirement_strings,
)
from helpers.workspace_graph import WorkspaceGraph

_FORCE_EXACT: Final = frozenset(
    {
        "python/pyproject.toml",
        "python/uv.lock",
        "python/.python-version",
    }
)
_FORCE_PREFIXES: Final = (".github/workflows/", "ci_scripts/")
_PYTHON: Final = "python"
_PROJECT_FILE: Final = "pyproject.toml"
_MEMBER_PATH_PARTS: Final = 3
_PROJECT_PATH_PARTS: Final = 4
_RENAME_COLUMNS: Final = 3
_STATUS_COLUMNS: Final = 2
_KIND_BY_DIR: Final[Mapping[str, Literal["package", "app"]]] = {
    "packages": "package",
    "apps": "app",
}


@dataclass(frozen=True)
class MemberLocation:
    """Where one repo path sits inside a workspace member.

    ``name`` is the directory name. ``is_project_file`` is true only for that
    member's ``pyproject.toml``.
    """

    kind: Literal["package", "app"]
    name: str
    is_project_file: bool


@dataclass(frozen=True)
class ProjectTexts:
    """The base and head text of one member ``pyproject.toml``.

    ``old`` is ``None`` when the file was added. ``new`` is ``None`` when it
    was deleted.
    """

    old: str | None
    new: str | None


@dataclass(frozen=True)
class ChangedMembers:
    """Directory names whose own files changed, before walking dependents."""

    packages: frozenset[str]
    apps: frozenset[str]


@dataclass(frozen=True)
class DependencySpec:
    """The fields of a member project that can change dependency resolution.

    Description, version, and ruff or pyright tables are not here.
    ``sources`` is the canonical JSON of ``tool.uv.sources``, or ``{}``.
    """

    requires_python: str | None
    dependencies: tuple[str, ...]
    optional_dependencies: tuple[RequirementGroup, ...]
    dependency_groups: tuple[RequirementGroup, ...]
    sources: str


@dataclass(frozen=True)
class Selection:
    """The packages and apps whose tests should run."""

    packages: tuple[str, ...]
    apps: tuple[str, ...]

    def to_json(self) -> dict[str, list[str]]:
        """Return the two lists in the CLI's JSON shape.

        Returns:
            ``packages`` and ``apps``, each sorted.
        """
        return {"packages": list(self.packages), "apps": list(self.apps)}


def every_member(graph: WorkspaceGraph) -> Selection:
    """Return every package and every app, each sorted.

    This is the result for a first push, whose base SHA is missing or all
    zeros, and for a change that can affect resolution outside one member:
    the root project, the lockfile, the Python version, a workflow, this
    selector, or a dependency-spec edit.

    Args:
        graph: Workspace members and depends-on edges.

    Returns:
        Both lists filled with every member directory name.
    """
    packages_asc_by_name = tuple(sorted(graph.packages))
    apps_asc_by_name = tuple(sorted(graph.apps))
    return Selection(packages_asc_by_name, apps_asc_by_name)


def select(
    graph: WorkspaceGraph,
    changed_paths: Sequence[str],
    project_texts_by_path: Mapping[str, ProjectTexts] | None = None,
) -> Selection:
    """Choose the members a set of changed paths affects.

    A file under ``python/packages/<name>/`` selects that package and every
    package or app that depends on it. The packages it depends on are not
    selected. A file under ``python/apps/<name>/`` selects that app only.
    A description or ruff edit of a member project stays on that rule. A
    change to ``requires-python``, a dependency list, or ``tool.uv.sources``
    selects every member, as do the root project, the lockfile, the Python
    version, ``.github/workflows/``, and ``ci_scripts/``.

    Args:
        graph: Workspace members and depends-on edges.
        changed_paths: Repo-relative paths, as ``git diff`` prints them.
        project_texts_by_path: Base and head text for each changed member
            ``pyproject.toml``, keyed by the repo-relative path.

    Returns:
        Sorted package and app directory names.

    Raises:
        SelectionError: A changed member ``pyproject.toml`` has no texts, or a
            text is not valid TOML.
    """
    paths = tuple(normalize_path(path) for path in changed_paths)
    if any(_is_force_all(path) for path in paths):
        return every_member(graph)
    if project_texts_by_path is None:
        project_texts_by_path = {}
    if _dependency_spec_changed(graph, paths, project_texts_by_path):
        return every_member(graph)
    changed = changed_members(graph, paths)
    reached = affected_nodes(graph, changed.packages)
    packages_asc_by_name = tuple(sorted(name for name in reached if name in graph.packages))
    apps_asc_by_name = tuple(
        sorted({name for name in reached if name in graph.apps} | changed.apps)
    )
    return Selection(packages_asc_by_name, apps_asc_by_name)


def changed_members(graph: WorkspaceGraph, paths: Sequence[str]) -> ChangedMembers:
    """Return the packages and apps whose own files appear in ``paths``.

    Does not walk dependents. A path outside ``python/packages`` and
    ``python/apps``, or under a directory that is not a workspace member, is
    ignored.

    Args:
        graph: Workspace members and depends-on edges.
        paths: Repo-relative paths with forward slashes.

    Returns:
        The directory names touched directly.
    """
    packages: set[str] = set()
    apps: set[str] = set()
    for path in paths:
        location = _known_member(graph, path)
        if location is None:
            continue
        if location.kind == "package":
            packages.add(location.name)
        else:
            apps.add(location.name)
    return ChangedMembers(frozenset(packages), frozenset(apps))


def paths_from_name_status(text: str) -> tuple[str, ...]:
    """Return every path in ``git diff --name-status`` output.

    A rename or copy contributes both paths.

    Args:
        text: The raw command output.

    Returns:
        Repo-relative paths, in the order the diff printed them.

    Raises:
        SelectionError: A line does not have the fields its status requires.
    """
    collected: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status[:1] in {"R", "C"}:
            if len(parts) < _RENAME_COLUMNS:
                raise SelectionError(f"A rename line is missing a path: {line!r}.")
            collected.extend(parts[1:_RENAME_COLUMNS])
        else:
            if len(parts) < _STATUS_COLUMNS:
                raise SelectionError(f"A diff line is missing a path: {line!r}.")
            collected.append(parts[1])
    return tuple(normalize_path(_unquote(path)) for path in collected)


def dependency_spec(text: str) -> DependencySpec:
    """Read the resolution-relevant fields of one member ``pyproject.toml``.

    The result contains ``requires-python``, the dependency strings,
    optional-dependencies, dependency-groups, and ``tool.uv.sources``.
    Description, version, and ruff or pyright tables are ignored.

    Args:
        text: The file contents.

    Returns:
        The fields that can change which versions the workspace resolves.

    Raises:
        SelectionError: ``text`` is not valid TOML, or a dependency field has
            the wrong shape.
    """
    try:
        loaded = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise SelectionError("A member pyproject.toml is not valid TOML.") from exc
    root = object_dict(loaded)
    if root is None:
        raise SelectionError("A member pyproject.toml is not a table.")
    project = object_dict(root.get("project")) or {}
    return DependencySpec(
        requires_python=_requires_python(project.get("requires-python")),
        dependencies=requirement_strings(project.get("dependencies")),
        optional_dependencies=requirement_groups(project.get("optional-dependencies")),
        dependency_groups=requirement_groups(root.get("dependency-groups")),
        sources=_sources(root.get("tool")),
    )


def dependency_spec_changed(texts: ProjectTexts) -> bool:
    """Return whether the two revisions can change dependency resolution.

    An added or deleted file counts as a change. A description-only or
    ruff-only edit does not.

    Args:
        texts: The base and head contents. ``None`` means the file is absent
            in that revision.

    Returns:
        ``True`` when the resolution-relevant fields differ.

    Raises:
        SelectionError: Either text is not valid TOML, or a dependency field
            has the wrong shape.
    """
    if texts.old is None or texts.new is None:
        return True
    return dependency_spec(texts.old) != dependency_spec(texts.new)


def parse_member_path(path: str) -> MemberLocation | None:
    """Return the member a repo-relative path belongs to.

    ``python/packages/<name>/...`` is a package. ``python/apps/<name>/...`` is
    an app. ``is_project_file`` is true only when the path is that member's
    ``pyproject.toml``. Any other path, including a blueprint or a scaffold
    script, returns ``None``.

    Args:
        path: A repo-relative path with forward slashes.

    Returns:
        The member location, or ``None`` when the path is outside a member.
    """
    parts = path.split("/")
    if len(parts) < _MEMBER_PATH_PARTS or parts[0] != _PYTHON:
        return None
    kind = _KIND_BY_DIR.get(parts[1])
    if kind is None or not parts[2]:
        return None
    is_project_file = len(parts) == _PROJECT_PATH_PARTS and parts[3] == _PROJECT_FILE
    return MemberLocation(kind=kind, name=parts[2], is_project_file=is_project_file)


def is_member_project_file(path: str) -> bool:
    """Return whether ``path`` is a package or app ``pyproject.toml``.

    Args:
        path: A repo-relative path with forward slashes.

    Returns:
        ``True`` for ``python/packages/<name>/pyproject.toml`` and the app form.
    """
    location = parse_member_path(path)
    return location is not None and location.is_project_file


def normalize_path(path: str) -> str:
    """Return a repo-relative path with forward slashes.

    Args:
        path: A diff path, possibly with a ``./`` prefix or backslashes.

    Returns:
        The path git would print on a POSIX machine.
    """
    text = path.replace("\\", "/")
    if text.startswith("./"):
        return text[2:]
    return text


def _is_force_all(path: str) -> bool:
    return path in _FORCE_EXACT or path.startswith(_FORCE_PREFIXES)


def _dependency_spec_changed(
    graph: WorkspaceGraph,
    paths: Sequence[str],
    project_texts_by_path: Mapping[str, ProjectTexts],
) -> bool:
    for path in paths:
        if _known_project(graph, path) is None:
            continue
        revision = project_texts_by_path.get(path)
        if revision is None:
            raise SelectionError(f"No base and head text for {path}.")
        if dependency_spec_changed(revision):
            return True
    return False


def _known_member(graph: WorkspaceGraph, path: str) -> MemberLocation | None:
    location = parse_member_path(path)
    if location is None:
        return None
    names = graph.packages if location.kind == "package" else graph.apps
    if location.name not in names:
        return None
    return location


def _known_project(graph: WorkspaceGraph, path: str) -> MemberLocation | None:
    location = _known_member(graph, path)
    if location is None or not location.is_project_file:
        return None
    return location


def _requires_python(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SelectionError("requires-python is not a string.")
    return value.strip()


def _sources(tool: object) -> str:
    """Return canonical JSON for ``tool.uv.sources``, or ``{}`` when absent."""
    if tool is None:
        return "{}"
    tool_table = object_dict(tool)
    if tool_table is None:
        raise SelectionError("tool is not a table.")
    uv = object_dict(tool_table.get("uv"))
    if tool_table.get("uv") is not None and uv is None:
        raise SelectionError("tool.uv is not a table.")
    if uv is None:
        return "{}"
    sources = uv.get("sources")
    if sources is None:
        return "{}"
    try:
        return json.dumps(sources, sort_keys=True)
    except TypeError as exc:
        raise SelectionError("tool.uv.sources cannot be compared.") from exc


def _unquote(path: str) -> str:
    if path.startswith('"') and path.endswith('"') and path != '"':
        return path[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return path
