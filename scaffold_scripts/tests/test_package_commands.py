"""Add, rename, and delete an empty package."""

from pathlib import Path

import pytest

from add_package import main as add_main
from delete_package import main as delete_main
from helpers.errors import ScaffoldError
from helpers.package_operations import add_package, delete_package, rename_package
from helpers.paths import RepoPaths, read_text, write_text
from rename_package import main as rename_main

_DESCRIPTION = (
    "Production-grade Python monorepo template built around dependency injection "
    "and zero global state. FastAPI, FastMCP, and task-runner blueprints share one "
    "workspace; structured logging, Prometheus, Kubernetes probes, and Alembic are "
    "written once."
)
_WORKSPACE = f"""\
[project]
name = "monorepo-template"
version = "1.0.0"
description = "{_DESCRIPTION}"
requires-python = ">=3.14,<3.15"
dependencies = [
    "shared-other",
]

[tool.uv.sources]
shared-other = {{ workspace = true }}

[tool.uv.workspace]
members = [
    "packages/other",
]

[tool.pytest.ini_options]
testpaths = [
    "packages/other/tests",
]

[tool.ruff]
src = [
    "packages/other/src",
    "packages/other/tests",
]

[tool.ruff.lint.isort]
known-first-party = [
    "shared_other",
]

[tool.ruff.lint.per-file-ignores]
"packages/other/tests/**/*.py" = ["S101", "S603", "PLR2004", "TRY301"]

[tool.pyright]
include = [
    "packages/other/src",
    "packages/other/tests",
]
extraPaths = [
    "packages/other/src",
]
"""


def _noop(python_dir: Path) -> None:
    """Skip the lock step."""


def _refuse(python_dir: Path) -> None:
    """Fail when a rejected command still refreshes the lock."""
    message = f"sync should not run in {python_dir}"
    raise AssertionError(message)


def _package_repo(tmp_path: Path) -> RepoPaths:
    root = tmp_path / "repo"
    python = root / "python"
    (python / "apps").mkdir(parents=True)
    (python / "packages").mkdir()
    write_text(root / "compose.yaml", "name: test\nservices:\n")
    write_text(root / ".env.example", "")
    write_text(python / "pyproject.toml", _WORKSPACE)
    return RepoPaths(root=root)


def test_add_writes_an_empty_package_without_test_init_files(tmp_path: Path) -> None:
    """The skeleton is importable and is registered in sorted workspace lists."""
    paths = _package_repo(tmp_path)
    compose = read_text(paths.compose_file)

    message = add_package(paths, "shared_widget", sync=_noop)

    package = paths.package_dir("widget")
    assert message == "Added package 'shared_widget' at python/packages/widget."
    assert (package / "src" / "shared_widget" / "__init__.py").is_file()
    assert (package / "src" / "shared_widget" / "py.typed").is_file()
    assert (package / "tests" / "shared_widget" / "test_import.py").is_file()
    assert not (package / "tests" / "__init__.py").exists()
    assert not (package / "tests" / "shared_widget" / "__init__.py").exists()
    project = read_text(package / "pyproject.toml")
    assert 'name = "shared-widget"\n' in project
    assert 'module-name = "shared_widget"\n' in project
    assert "dependencies" not in project
    workspace = read_text(paths.workspace_pyproject)
    assert workspace.index('"shared-other"') < workspace.index('"shared-widget"')
    assert workspace.index('"packages/other"') < workspace.index('"packages/widget"')
    assert '"packages/widget/tests"' in workspace
    assert '"shared_widget"' in workspace
    assert read_text(paths.compose_file) == compose
    assert read_text(paths.env_example) == ""


def test_add_rejects_a_duplicate_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A second package with the same directory is refused before the lock step."""
    paths = _package_repo(tmp_path)
    paths.package_dir("widget").mkdir()

    with pytest.raises(SystemExit) as caught:
        add_main(["shared_widget"], paths=paths, sync=_refuse)

    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert error == "Package 'shared_widget' already exists at python/packages/widget.\n"


def test_rename_rewrites_imports_and_template_paths(tmp_path: Path) -> None:
    """Consumers and template path sources follow the new import and directory."""
    paths = _package_repo(tmp_path)
    add_package(paths, "shared_widget", sync=_noop)
    consumer = paths.app_dir("billing_api") / "src" / "billing_api" / "use.py"
    consumer.parent.mkdir(parents=True)
    write_text(consumer, "from shared_widget import value\n")
    template = paths.template_dir("fastapi")
    template.mkdir(parents=True)
    write_text(
        template / "pyproject.toml",
        "\n".join(
            (
                "[project]",
                'name = "app"',
                "dependencies = [",
                '    "shared-widget",',
                "]",
                "",
                "[tool.uv.sources]",
                'shared-widget = { path = "../../packages/widget" }',
                "",
            ),
        ),
    )

    message = rename_package(paths, "shared_widget", "shared_gadget", sync=_noop)

    assert message == "Renamed 'shared_widget' to 'shared_gadget'."
    assert not paths.package_dir("widget").exists()
    renamed = paths.package_dir("gadget")
    assert (renamed / "src" / "shared_gadget" / "__init__.py").is_file()
    assert not (renamed / "src" / "shared_widget").exists()
    assert read_text(consumer) == "from shared_gadget import value\n"
    template_text = read_text(template / "pyproject.toml")
    assert 'shared-gadget = { path = "../../packages/gadget" }' in template_text
    assert "shared-widget" not in template_text
    assert "shared_gadget" not in template_text
    workspace = read_text(paths.workspace_pyproject)
    assert '"packages/gadget"' in workspace
    assert '"packages/widget"' not in workspace
    assert '"shared_gadget"' in workspace
    assert "shared-gadget = { workspace = true }" in workspace


def test_rename_can_keep_the_directory(tmp_path: Path) -> None:
    """Adding a shared_ prefix does not move packages/<name>."""
    paths = _package_repo(tmp_path)
    add_package(paths, "widget", sync=_noop)

    rename_package(paths, "widget", "shared_widget", sync=_noop)

    package = paths.package_dir("widget")
    assert package.is_dir()
    assert not paths.package_dir("shared_widget").exists()
    assert (package / "src" / "shared_widget" / "__init__.py").is_file()
    project = read_text(package / "pyproject.toml")
    assert 'name = "shared-widget"\n' in project
    assert 'module-name = "shared_widget"\n' in project
    assert 'description = "shared_widget package."\n' in project
    workspace = read_text(paths.workspace_pyproject)
    assert '"packages/widget"' in workspace
    assert '"packages/shared_widget"' not in workspace
    assert "shared-widget = { workspace = true }" in workspace
    assert '"shared_widget"' in workspace


def test_delete_refuses_while_a_member_depends_on_the_package(tmp_path: Path) -> None:
    """A dependency in another member keeps the package on disk."""
    paths = _package_repo(tmp_path)
    add_package(paths, "shared_widget", sync=_noop)
    before = read_text(paths.workspace_pyproject)
    app = paths.app_dir("billing_api")
    app.mkdir()
    write_text(
        app / "pyproject.toml",
        '[project]\nname = "billing-api"\ndependencies = [\n    "shared-widget",\n]\n',
    )

    with pytest.raises(ScaffoldError, match="still required by billing_api"):
        delete_package(paths, "shared_widget", sync=_refuse)

    assert paths.package_dir("widget").is_dir()
    assert read_text(paths.workspace_pyproject) == before


def test_delete_refuses_a_template_path_without_a_member_dependency(tmp_path: Path) -> None:
    """A blueprint path source is a dependent even when no app lists the package."""
    paths = _package_repo(tmp_path)
    add_package(paths, "shared_widget", sync=_noop)
    template = paths.template_dir("fastapi")
    template.mkdir(parents=True)
    write_text(
        template / "pyproject.toml",
        '[tool.uv.sources]\nshared-widget = { path = "../../packages/widget" }\n',
    )

    with pytest.raises(ScaffoldError, match="still required by template fastapi"):
        delete_package(paths, "shared_widget", sync=_refuse)

    assert paths.package_dir("widget").is_dir()


def test_delete_refuses_an_import_without_a_dependency(tmp_path: Path) -> None:
    """An import statement counts even when the project file forgot the dependency."""
    paths = _package_repo(tmp_path)
    add_package(paths, "shared_widget", sync=_noop)
    consumer = paths.app_dir("billing_api") / "src" / "billing_api" / "use.py"
    consumer.parent.mkdir(parents=True)
    write_text(consumer, "import shared_widget\n")

    with pytest.raises(ScaffoldError, match="still required by billing_api"):
        delete_package(paths, "shared_widget", sync=_refuse)


def test_delete_removes_extras_that_add_did_not_create(tmp_path: Path) -> None:
    """Alembic ignores, pythonpath, and a package execution environment go too."""
    paths = _package_repo(tmp_path)
    add_package(paths, "shared_widget", sync=_noop)
    workspace = read_text(paths.workspace_pyproject)
    workspace = workspace.replace(
        '"packages/widget/tests",\n',
        '"packages/widget/tests",\n    "packages/widget/alembic",\n',
        1,
    )
    workspace = workspace.replace(
        "[tool.pytest.ini_options]\n",
        '[tool.pytest.ini_options]\npythonpath = ["packages/widget/tests/fakes"]\n',
        1,
    )
    workspace = workspace.replace(
        '"packages/other/tests/**/*.py" = ["S101", "S603", "PLR2004", "TRY301"]\n',
        "\n".join(
            (
                '"packages/other/tests/**/*.py" = ["S101", "S603", "PLR2004", "TRY301"]',
                '"packages/widget/alembic/versions/*.py" = ["D", "ANN", "UP", "I"]',
                "",
            ),
        ),
    )
    workspace += (
        "\n[[tool.pyright.executionEnvironments]]\n"
        'root = "packages/widget/tests"\n'
        'extraPaths = ["packages/widget/src", "packages/widget/tests/fakes"]\n'
    )
    write_text(paths.workspace_pyproject, workspace)

    message = delete_package(paths, "shared_widget", sync=_noop)

    assert message == "Deleted package 'shared_widget'."
    assert not paths.package_dir("widget").exists()
    remaining = read_text(paths.workspace_pyproject)
    assert "packages/widget" not in remaining
    assert "shared-widget" not in remaining
    assert "shared_widget" not in remaining
    assert '"packages/other"' in remaining
    assert "pythonpath" not in remaining
    assert "executionEnvironments" not in remaining


def test_delete_reports_a_missing_package(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Delete does not invent a package in order to remove it."""
    with pytest.raises(SystemExit) as caught:
        delete_main(["shared_widget"], paths=_package_repo(tmp_path), sync=_refuse)

    assert caught.value.code == 1
    assert capsys.readouterr().err == "Package 'shared_widget' does not exist.\n"


def test_rename_reports_a_missing_package(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rename does not create the target when the source is absent."""
    with pytest.raises(SystemExit) as caught:
        rename_main(["shared_widget", "shared_gadget"], paths=_package_repo(tmp_path), sync=_refuse)

    assert caught.value.code == 1
    assert capsys.readouterr().err == "Package 'shared_widget' does not exist.\n"
