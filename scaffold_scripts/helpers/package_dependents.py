"""Find apps, packages, and templates that still use one package."""

import re
import tomllib
from pathlib import Path
from typing import cast

from helpers.errors import ScaffoldError
from helpers.package_names import PackageIdentity
from helpers.paths import RepoPaths, iter_files, read_text
from helpers.requirements import normalize_distribution, requirement_name


def dependent_names(paths: RepoPaths, identity: PackageIdentity) -> list[str]:
    """Return who still uses ``identity``, outside the package itself.

    A workspace member counts when its dependencies, optional-dependencies,
    or dependency-groups name the distribution, or its project file points
    at ``packages/<directory>``. A template counts the same way. A Python
    file counts when it imports the module. The workspace root's dependency
    list does not count. Names are sorted.
    """
    labels: set[str] = set()
    package_root = paths.package_dir(identity.directory)
    for project in _member_projects(paths):
        if project.parent == package_root:
            continue
        if _project_requires(read_text(project), project, identity):
            labels.add(project.parent.name)
    for project in _template_projects(paths):
        if _project_requires(read_text(project), project, identity):
            labels.add(f"template {project.parent.name}")
    for path in _python_files(paths.python_dir):
        if _is_inside(path, package_root):
            continue
        if imports_module(read_text(path), identity.import_name):
            labels.add(_label(paths.python_dir, path))
    labels_asc_by_name = sorted(labels)
    return labels_asc_by_name  # noqa: RET504


def imports_module(text: str, import_name: str) -> bool:
    """Return whether ``text`` imports ``import_name`` as a module."""
    pattern = re.compile(
        rf"(?m)^[ \t]*(?:from|import)[ \t]+{re.escape(import_name)}(?![A-Za-z0-9_])",
    )
    return pattern.search(text) is not None


def _project_requires(text: str, path: Path, identity: PackageIdentity) -> bool:
    if _mentions_package_path(text, identity.directory):
        return True
    expected = normalize_distribution(identity.distribution_name)
    return any(requirement_name(item) == expected for item in _requirement_strings(text, path))


def _mentions_package_path(text: str, directory: str) -> bool:
    return re.search(rf"packages/{re.escape(directory)}(?=/|\"|$)", text) is not None


def _requirement_strings(text: str, path: Path) -> tuple[str, ...]:
    table = _load_table(text, path)
    strings: list[str] = []
    project = _object_dict(table.get("project"))
    if project is not None:
        strings.extend(_string_list(project.get("dependencies")))
        strings.extend(_group_strings(project.get("optional-dependencies")))
    strings.extend(_group_strings(table.get("dependency-groups")))
    return tuple(strings)


def _load_table(text: str, path: Path) -> dict[str, object]:
    try:
        loaded: object = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ScaffoldError(f"{path.as_posix()} is not valid TOML.") from exc
    table = _object_dict(loaded)
    if table is None:
        raise ScaffoldError(f"{path.as_posix()} is not a table.")
    return table


def _object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    items = cast("dict[object, object]", value)
    return {str(key): item for key, item in items.items()}


def _group_strings(value: object) -> list[str]:
    requirement_list_by_group = _object_dict(value)
    if requirement_list_by_group is None:
        return []
    strings: list[str] = []
    for group in requirement_list_by_group.values():
        strings.extend(_string_list(group))
    return strings


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        message = "A dependency list is not a list of strings."
        raise ScaffoldError(message)
    strings: list[str] = []
    for item in cast("list[object]", value):
        if not isinstance(item, str):
            message = "A dependency list is not a list of strings."
            raise ScaffoldError(message)
        strings.append(item)
    return strings


def _member_projects(paths: RepoPaths) -> list[Path]:
    projects: list[Path] = []
    for root in (paths.packages_dir, paths.apps_dir):
        if not root.is_dir():
            continue
        project_paths_asc_by_path = sorted(
            path for path in root.glob("*/pyproject.toml") if path.is_file()
        )
        projects.extend(project_paths_asc_by_path)
    return projects


def _template_projects(paths: RepoPaths) -> list[Path]:
    root = paths.python_dir / "_templates"
    if not root.is_dir():
        return []
    project_paths_asc_by_path = sorted(
        path for path in root.glob("*/pyproject.toml") if path.is_file()
    )
    return project_paths_asc_by_path  # noqa: RET504


def _python_files(root: Path) -> list[Path]:
    return [path for path in iter_files(root) if path.suffix == ".py"]


def _is_inside(path: Path, root: Path) -> bool:
    if not root.exists():
        return False
    return path.resolve().is_relative_to(root.resolve())


def _label(python_dir: Path, path: Path) -> str:
    relative = path.relative_to(python_dir)
    parts = relative.parts
    if len(parts) > 1 and parts[0] in {"packages", "apps"}:
        return parts[1]
    if len(parts) > 1 and parts[0] == "_templates":
        return f"template {parts[1]}"
    return relative.as_posix()
