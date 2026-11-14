"""Add, rename, and delete one app across the repo files those commands share."""

import shutil

from helpers.compose_leftovers import compose_leftover_lines, leftover_report
from helpers.copy_template import install_template, rename_installed_tree
from helpers.env_example import add_app_env, remove_app_env, rename_app_env
from helpers.errors import ScaffoldError, already_exists_message, missing_message
from helpers.names import (
    TASK_RUNNER,
    AppIdentity,
    category_from_pyproject,
    next_app_port,
    require_app_name,
    require_category,
    require_port,
)
from helpers.paths import RepoPaths, read_text, write_text
from helpers.sync import Sort, Sync, run_sync, sort_imports
from helpers.workspace_toml import add_workspace_app, remove_workspace_app, rename_workspace_app


def add_app(
    paths: RepoPaths,
    category: str,
    name: str,
    *,
    sync: Sync | None = None,
    sort: Sort | None = None,
) -> str:
    """Copy a template and register the new app.

    The command checks the name and the destination before it writes. The
    published port is one above the highest ``<APP>__SERVER__PORT`` in
    ``.env.example`` and ``compose.yaml``, and at least 8081. ``compose.yaml``
    is only read. The caller updates it after this command succeeds.

    After the lock step, the new app's import blocks are re-sorted, because
    the blueprint was sorted for the package name ``app``. ``sync`` and
    ``sort`` replace those two steps in tests. A replacement ``sync`` with no
    ``sort`` skips sorting too, since ruff needs the app installed.

    Returns:
        The one-line success report, including the assigned port.

    Raises:
        ScaffoldError: The name is invalid, the category is unknown, or the
            app directory already exists.
    """
    category = require_category(category)
    name = require_app_name(name)
    if paths.app_dir(name).exists():
        raise ScaffoldError(already_exists_message(name))
    template = paths.template_dir(category)
    if not template.is_dir():
        message = f"Category {category!r} has no template at python/_templates/{category}."
        raise ScaffoldError(message)
    env_text = read_text(paths.env_example)
    compose_text = read_text(paths.compose_file)
    workspace_original = read_text(paths.workspace_pyproject)
    port = None if category == TASK_RUNNER else next_app_port(env_text, compose_text)
    identity = AppIdentity(name=name, category=category, port=port)
    workspace_text = add_workspace_app(workspace_original, identity)
    env_updated = add_app_env(env_text, identity)
    paths.apps_dir.mkdir(parents=True, exist_ok=True)
    try:
        install_template(paths, identity)
        write_text(paths.workspace_pyproject, workspace_text)
        write_text(paths.env_example, env_updated)
    except Exception:
        shutil.rmtree(paths.app_dir(name), ignore_errors=True)
        _restore(paths, workspace_original, env_text)
        raise
    _sync_and_sort(paths, name, sync, sort)
    if identity.port is None:
        return f"Added {identity.category} app '{identity.name}'."
    return f"Added {identity.category} app '{identity.name}' on port {identity.port}."


def rename_app(
    paths: RepoPaths,
    source_name: str,
    target_name: str,
    *,
    sync: Sync | None = None,
    sort: Sort | None = None,
) -> str:
    """Rename an app and keep its category and port.

    Raises:
        ScaffoldError: The source app is missing, or the target name is
            already an app directory.
    """
    source_name = require_app_name(source_name)
    target_name = require_app_name(target_name)
    source_dir = paths.app_dir(source_name)
    if not source_dir.is_dir():
        raise ScaffoldError(missing_message(source_name))
    if paths.app_dir(target_name).exists():
        raise ScaffoldError(already_exists_message(target_name))
    env_text = read_text(paths.env_example)
    workspace_original = read_text(paths.workspace_pyproject)
    category = category_from_pyproject(read_text(source_dir / "pyproject.toml"))
    port = None if category == TASK_RUNNER else require_port(env_text, source_name)
    source = AppIdentity(
        name=source_name,
        category=category,
        port=port,
    )
    target = AppIdentity(name=target_name, category=source.category, port=source.port)
    workspace_text = rename_workspace_app(workspace_original, source, target)
    env_updated = rename_app_env(env_text, source, target)
    rename_installed_tree(source_dir, source, target)
    try:
        write_text(paths.workspace_pyproject, workspace_text)
        write_text(paths.env_example, env_updated)
    except Exception:
        if paths.app_dir(target_name).is_dir():
            rename_installed_tree(paths.app_dir(target_name), target, source)
        _restore(paths, workspace_original, env_text)
        raise
    _sync_and_sort(paths, target_name, sync, sort)
    return f"Renamed '{source_name}' to '{target_name}'."


def delete_app(paths: RepoPaths, name: str, *, sync: Sync | None = None) -> str:
    """Delete an app directory and its workspace and env lines.

    ``compose.yaml`` is left as it is. The caller removes the app service,
    and a migrate service only when no remaining app uses that database.
    When Compose still names the app, the report gains a second line with
    the line numbers so that step is not forgotten.

    Returns:
        The success line, followed by the Compose leftover line when there
        is one.

    Raises:
        ScaffoldError: The app directory does not exist.
    """
    name = require_app_name(name)
    app_dir = paths.app_dir(name)
    if not app_dir.is_dir():
        raise ScaffoldError(missing_message(name))
    identity = AppIdentity(
        name=name,
        category=category_from_pyproject(read_text(app_dir / "pyproject.toml")),
        port=None,
    )
    workspace_original = read_text(paths.workspace_pyproject)
    env_text = read_text(paths.env_example)
    workspace_text = remove_workspace_app(workspace_original, identity)
    env_updated = remove_app_env(env_text, identity)
    try:
        write_text(paths.workspace_pyproject, workspace_text)
        write_text(paths.env_example, env_updated)
        shutil.rmtree(app_dir)
    except Exception:
        _restore(paths, workspace_original, env_text)
        raise
    run_sync(paths.python_dir, sync)
    report = f"Deleted app '{name}'."
    leftovers = compose_leftover_lines(read_text(paths.compose_file), identity)
    if leftovers:
        report += "\n" + leftover_report(identity, leftovers)
    return report


def _restore(paths: RepoPaths, workspace: str, env: str) -> None:
    """Put the workspace and env example back after a failed command."""
    write_text(paths.workspace_pyproject, workspace)
    write_text(paths.env_example, env)


def _sync_and_sort(paths: RepoPaths, name: str, sync: Sync | None, sort: Sort | None) -> None:
    """Lock, sync, and then re-sort the imports of ``name``.

    Sorting needs the app installed so ruff resolves its first-party modules,
    which is why it follows the lock step. In production both are ``None``
    and the real commands run. A test passes both to record the order, or
    only ``sync`` to skip the tree rewrite entirely.
    """
    run_sync(paths.python_dir, sync)
    if sort is not None:
        sort(paths.python_dir, paths.app_dir(name))
    elif sync is None:
        sort_imports(paths.python_dir, paths.app_dir(name))
