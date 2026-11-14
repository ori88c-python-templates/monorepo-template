"""Copy a blueprint into ``python/apps`` and rename an installed app tree."""

import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Final

from helpers.dockerfiles import set_image_command, set_published_port, use_apps_copy
from helpers.errors import ScaffoldError
from helpers.names import FASTAPI, FASTMCP, TASK_RUNNER, AppIdentity, replace_identity
from helpers.paths import RepoPaths, ignore_skipped, iter_files, read_text, write_text

_APP_NAME: Final = re.compile(r'(?m)^APP_NAME: Final = "([a-z][a-z0-9_]*)"\s*$')
_EXPOSE: Final = re.compile(r"(?m)^EXPOSE (\d+)\s*$")
_LABEL_BY_CATEGORY: Final = {FASTAPI: "FastAPI", FASTMCP: "FastMCP", TASK_RUNNER: "Task runner"}


def install_template(paths: RepoPaths, identity: AppIdentity) -> None:
    """Copy ``_templates/<category>`` and make it speak as ``identity``.

    The blueprint keeps the import package ``app`` and a proof app name in
    its constants, README, and image. The installed tree uses the new
    directory name, a hyphenated distribution name, and workspace sources.
    """
    destination = paths.app_dir(identity.name)
    shutil.copytree(paths.template_dir(identity.category), destination, ignore=ignore_skipped)
    proof = _proof_identity(destination, identity.category)
    _rewrite_tree(
        destination, lambda path, text: _added_text(path, text, destination, proof, identity)
    )
    _rename_package(destination, "app", identity.name)


def rename_installed_tree(source_dir: Path, source: AppIdentity, target: AppIdentity) -> Path:
    """Rename import tokens inside ``source_dir`` and then rename the directory.

    Returns the directory under its new name. The published port is unchanged.
    """
    _rewrite_tree(
        source_dir,
        lambda path, text: _renamed_text(path, text, source, target),
    )
    _rename_package(source_dir, source.name, target.name)
    destination = source_dir.with_name(target.name)
    source_dir.rename(destination)
    return destination


def _added_text(
    path: Path,
    text: str,
    app_dir: Path,
    proof: AppIdentity,
    identity: AppIdentity,
) -> str:
    text = replace_identity(text, proof, identity)
    text = _rewrite_imports(text, identity.name)
    if path.name == "pyproject.toml":
        text = _finalize_new_pyproject(text, identity)
    if path.name == "Dockerfile":
        text = use_apps_copy(text)
        text = set_image_command(text, identity.distribution_name)
        if proof.port is not None and identity.port is not None:
            text = set_published_port(text, proof.port, identity.port)
    if path == app_dir / "README.md":
        text = _rewrite_readme_opening(text, identity)
    if path == app_dir / "src" / "app" / "__init__.py":
        text = _set_package_docstring(text, identity.name)
    return text


def _renamed_text(path: Path, text: str, source: AppIdentity, target: AppIdentity) -> str:
    text = replace_identity(text, source, target)
    if path.name == "pyproject.toml":
        text = _refresh_distribution_slots(text, target)
    if path.name == "Dockerfile":
        text = use_apps_copy(text)
        text = set_image_command(text, target.distribution_name)
    return text


def _proof_identity(app_dir: Path, category: str) -> AppIdentity:
    consts_path = app_dir / "src" / "app" / "config" / "app_consts.py"
    if not consts_path.is_file():
        message = f"Template {category} has no src/app/config/app_consts.py."
        raise ScaffoldError(message)
    name_match = _APP_NAME.search(read_text(consts_path))
    if name_match is None:
        message = f"Template {category} has no APP_NAME constant."
        raise ScaffoldError(message)
    if category == TASK_RUNNER:
        return AppIdentity(name=name_match.group(1), category=category, port=None)
    dockerfile = app_dir / "Dockerfile"
    expose = _EXPOSE.search(read_text(dockerfile))
    if expose is None:
        message = f"Template {category} Dockerfile has no EXPOSE port."
        raise ScaffoldError(message)
    return AppIdentity(name=name_match.group(1), category=category, port=int(expose.group(1)))


def _rewrite_tree(root: Path, transform: Callable[[Path, str], str]) -> None:
    for path in iter_files(root):
        try:
            original = read_text(path)
        except UnicodeDecodeError:
            continue
        updated = transform(path, original)
        if updated != original:
            write_text(path, updated)


def _rewrite_import_linter(text: str, name: str) -> str:
    """Point the layer contract at ``name`` instead of the blueprint package ``app``."""
    marker = "[tool.importlinter]\n"
    index = text.find(marker)
    if index == -1:
        return text
    head = text[:index]
    tail = text[index:]
    tail = tail.replace('root_package = "app"', f'root_package = "{name}"')
    tail = tail.replace('containers = ["app"]', f'containers = ["{name}"]')
    tail = tail.replace('"app.', f'"{name}.')
    return head + tail


def _rewrite_imports(text: str, name: str) -> str:
    """Rename the blueprint import package ``app`` to ``name``."""
    text = text.replace("from app.", f"from {name}.")
    text = text.replace("import app.", f"import {name}.")
    text = re.sub(r"\bfrom app import\b", f"from {name} import", text)
    text = re.sub(r"(?<![\w.])import app\b", f"import {name}", text)
    text = text.replace("app.main:", f"{name}.main:")
    text = text.replace("src/app/", f"src/{name}/")
    return text.replace('\n    "app",\n', f'\n    "{name}",\n')


def _finalize_new_pyproject(text: str, identity: AppIdentity) -> str:
    kind = _LABEL_BY_CATEGORY[identity.category]
    description = f"{kind} app. Distribution {identity.distribution_name}."
    text = re.sub(r'(?m)^name = "[^"]*"', f'name = "{identity.distribution_name}"', text, count=1)
    text = re.sub(r'(?m)^description = "[^"]*"', f'description = "{description}"', text, count=1)
    text = _refresh_distribution_slots(text, identity)
    text = re.sub(r'\{ path = "[^"]+" \}', "{ workspace = true }", text)
    return _rewrite_import_linter(text, identity.name)


def _refresh_distribution_slots(text: str, identity: AppIdentity) -> str:
    """Set the project name, console script, and module name from ``identity``."""
    text = re.sub(r'(?m)^name = "[^"]*"', f'name = "{identity.distribution_name}"', text, count=1)
    script = f'{identity.distribution_name} = "{identity.name}.main:main"\n'
    text = re.sub(
        r"(?ms)^\[project\.scripts\]\n.*?(?=^\[)",
        f"[project.scripts]\n{script}\n",
        text,
        count=1,
    )
    return re.sub(r'(?m)^module-name = "[^"]*"', f'module-name = "{identity.name}"', text, count=1)


def _rewrite_readme_opening(text: str, identity: AppIdentity) -> str:
    marker = "\nShared packages supply"
    index = text.find(marker)
    if index == -1:
        message = "Template README has no shared-packages section."
        raise ScaffoldError(message)
    kind = _LABEL_BY_CATEGORY[identity.category]
    opening = (
        f"# {identity.name}\n"
        "\n"
        f"{kind} app. Distribution `{identity.distribution_name}`. "
        f"Import package `{identity.name}`.\n"
        "\n"
    )
    return opening + text[index + 1 :]


def _set_package_docstring(text: str, name: str) -> str:
    updated, count = re.subn(
        r'^""".*?"""',
        f'"""{name} application package."""',
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        message = f"Package __init__.py has no docstring to set for {name}."
        raise ScaffoldError(message)
    return updated


def _rename_package(app_dir: Path, old: str, new: str) -> None:
    source = app_dir / "src" / old
    destination = app_dir / "src" / new
    if source == destination:
        return
    if not source.is_dir():
        message = f"Import package src/{old} is missing in {app_dir.name}."
        raise ScaffoldError(message)
    source.rename(destination)
