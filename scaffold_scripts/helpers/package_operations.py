"""Add, rename, and delete one shared package."""

import re
import shutil
from pathlib import Path

from helpers.errors import (
    ScaffoldError,
    package_exists,
    package_exists_at,
    package_missing,
    package_required_by,
)
from helpers.package_dependents import dependent_names
from helpers.package_files import write_package_skeleton
from helpers.package_names import PackageIdentity, identity_for_new_package, require_import_name
from helpers.package_rewrite import restore_rewrites, rewrite_package_tree
from helpers.package_workspace import add_workspace_package, remove_workspace_package
from helpers.paths import RepoPaths, read_text, write_text
from helpers.sync import Sync, run_sync

_MODULE_NAME = re.compile(r'(?m)^module-name = "([^"]+)"\s*$')
_PROJECT_NAME = re.compile(r'(?m)^name = "([^"]+)"\s*$')


def add_package(paths: RepoPaths, import_name: str, *, sync: Sync | None = None) -> str:
    """Create an empty package and register it.

    The directory drops a leading ``shared_``. The command checks the name
    before it writes, then runs the lock step.

    Returns:
        The one-line success report, including the directory.

    Raises:
        ScaffoldError: The name is invalid, or the directory, import, or
            distribution is already taken.
    """
    identity = identity_for_new_package(import_name)
    _reject_new(paths, identity)
    workspace_original = read_text(paths.workspace_pyproject)
    _reject_registered(workspace_original, identity)
    workspace_text = add_workspace_package(workspace_original, identity)
    paths.packages_dir.mkdir(parents=True, exist_ok=True)
    try:
        write_package_skeleton(paths.package_dir(identity.directory), identity)
        write_text(paths.workspace_pyproject, workspace_text)
    except Exception:
        shutil.rmtree(paths.package_dir(identity.directory), ignore_errors=True)
        write_text(paths.workspace_pyproject, workspace_original)
        raise
    run_sync(paths.python_dir, sync)
    return f"Added package '{identity.import_name}' at python/packages/{identity.directory}."


def rename_package(
    paths: RepoPaths,
    source_name: str,
    target_name: str,
    *,
    sync: Sync | None = None,
) -> str:
    """Rename a package's directory, import, and distribution.

    Python files and project files under ``python/`` are rewritten. The
    directory stays when only the ``shared_`` prefix changes.

    Raises:
        ScaffoldError: The source package is missing, or the target identity
            is already taken.
    """
    source = find_package(paths, require_import_name(source_name))
    target = identity_for_new_package(target_name)
    _reject_rename(paths, source, target)
    package_dir = paths.package_dir(source.directory)
    changed: list[tuple[Path, str]] = []
    src_renamed = False
    dir_renamed = False
    try:
        changed = rewrite_package_tree(paths.python_dir, package_dir, source, target)
        src_renamed = _rename_import_dir(package_dir, source.import_name, target.import_name)
        if source.directory != target.directory:
            package_dir.rename(paths.package_dir(target.directory))
            dir_renamed = True
    except Exception:
        _rollback_rename(paths, source, target, changed, (src_renamed, dir_renamed))
        raise
    run_sync(paths.python_dir, sync)
    return f"Renamed '{source.import_name}' to '{target.import_name}'."


def delete_package(paths: RepoPaths, import_name: str, *, sync: Sync | None = None) -> str:
    """Delete a package that nothing else requires.

    The check runs before any write. There is no confirmation flag.

    Raises:
        ScaffoldError: The package is missing, or an app, package, or template
            still requires it.
    """
    identity = find_package(paths, require_import_name(import_name))
    required_by = dependent_names(paths, identity)
    if required_by:
        raise ScaffoldError(package_required_by(identity.import_name, required_by))
    package_dir = paths.package_dir(identity.directory)
    workspace_original = read_text(paths.workspace_pyproject)
    workspace_text = remove_workspace_package(workspace_original, identity)
    try:
        write_text(paths.workspace_pyproject, workspace_text)
        shutil.rmtree(package_dir)
    except Exception:
        write_text(paths.workspace_pyproject, workspace_original)
        raise
    run_sync(paths.python_dir, sync)
    return f"Deleted package '{identity.import_name}'."


def find_package(paths: RepoPaths, import_name: str) -> PackageIdentity:
    """Return the installed package whose module name is ``import_name``.

    Raises:
        ScaffoldError: No package has that module name, or more than one does.
    """
    matches = [item for item in installed_packages(paths) if item.import_name == import_name]
    if not matches:
        raise ScaffoldError(package_missing(import_name))
    if len(matches) > 1:
        raise ScaffoldError(package_exists(import_name))
    return matches[0]


def installed_packages(paths: RepoPaths) -> list[PackageIdentity]:
    """Return packages that declare ``module-name`` and ``project.name``."""
    if not paths.packages_dir.is_dir():
        return []
    found: list[PackageIdentity] = []
    project_files_asc_by_path = sorted(paths.packages_dir.glob("*/pyproject.toml"))
    for project in project_files_asc_by_path:
        identity = _identity_from_project(project.parent.name, read_text(project))
        if identity is not None:
            found.append(identity)
    return found


def _identity_from_project(directory: str, text: str) -> PackageIdentity | None:
    module = _MODULE_NAME.search(text)
    name = _PROJECT_NAME.search(text)
    if module is None or name is None:
        return None
    return PackageIdentity(
        import_name=module.group(1),
        directory=directory,
        distribution_name=name.group(1),
    )


def _reject_new(paths: RepoPaths, identity: PackageIdentity) -> None:
    if paths.package_dir(identity.directory).exists():
        raise ScaffoldError(package_exists_at(identity.import_name, identity.directory))
    if paths.app_dir(identity.directory).exists():
        raise ScaffoldError(package_exists(identity.import_name))
    for existing in installed_packages(paths):
        if existing.directory == identity.directory:
            raise ScaffoldError(package_exists_at(identity.import_name, identity.directory))
        same_name = existing.import_name == identity.import_name
        same_distribution = existing.distribution_name == identity.distribution_name
        if same_name or same_distribution:
            raise ScaffoldError(package_exists(identity.import_name))


def _reject_registered(text: str, identity: PackageIdentity) -> None:
    if f'"packages/{identity.directory}"' in text:
        raise ScaffoldError(package_exists_at(identity.import_name, identity.directory))
    if f"{identity.distribution_name} = {{ workspace = true }}" in text:
        raise ScaffoldError(package_exists(identity.import_name))


def _reject_rename(paths: RepoPaths, source: PackageIdentity, target: PackageIdentity) -> None:
    if source.import_name == target.import_name:
        raise ScaffoldError(package_exists_at(target.import_name, target.directory))
    if source.directory != target.directory and paths.package_dir(target.directory).exists():
        raise ScaffoldError(package_exists_at(target.import_name, target.directory))
    if source.directory != target.directory and paths.app_dir(target.directory).exists():
        raise ScaffoldError(package_exists(target.import_name))
    for existing in installed_packages(paths):
        if existing.import_name == source.import_name and existing.directory == source.directory:
            continue
        if existing.directory == target.directory and existing.directory != source.directory:
            raise ScaffoldError(package_exists_at(target.import_name, target.directory))
        same_name = existing.import_name == target.import_name
        same_distribution = existing.distribution_name == target.distribution_name
        if same_name or same_distribution:
            raise ScaffoldError(package_exists(target.import_name))
    destination = paths.package_dir(source.directory) / "src" / target.import_name
    if target.import_name != source.import_name and destination.exists():
        raise ScaffoldError(package_exists(target.import_name))


def _rename_import_dir(package_dir: Path, source: str, target: str) -> bool:
    if source == target:
        return False
    src = package_dir / "src" / source
    if not src.is_dir():
        return False
    src.rename(package_dir / "src" / target)
    return True


def _rollback_rename(
    paths: RepoPaths,
    source: PackageIdentity,
    target: PackageIdentity,
    changed: list[tuple[Path, str]],
    renamed: tuple[bool, bool],
) -> None:
    src_renamed, dir_renamed = renamed
    current = paths.package_dir(target.directory if dir_renamed else source.directory)
    if dir_renamed and current.is_dir():
        current.rename(paths.package_dir(source.directory))
        current = paths.package_dir(source.directory)
    if src_renamed:
        moved = current / "src" / target.import_name
        if moved.is_dir():
            moved.rename(current / "src" / source.import_name)
    restore_rewrites(changed)
