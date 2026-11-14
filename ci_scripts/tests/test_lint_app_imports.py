"""Discovery of installed app import-linter configs."""

from pathlib import Path

import pytest

from lint_app_imports import app_configs, lint_installed_apps


def test_app_configs_are_sorted_and_skip_templates(tmp_path: Path) -> None:
    """Only ``python/apps/<name>/pyproject.toml`` is returned, in directory order."""
    python_dir = tmp_path / "python"
    for name in ("shop_mcp", "orders_api"):
        path = python_dir / "apps" / name
        path.mkdir(parents=True)
        (path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    template = python_dir / "_templates" / "fastapi"
    template.mkdir(parents=True)
    (template / "pyproject.toml").write_text("[project]\nname = 'app'\n", encoding="utf-8")

    found = app_configs(python_dir)

    assert [path.parent.name for path in found] == ["orders_api", "shop_mcp"]


def test_missing_apps_directory_is_empty(tmp_path: Path) -> None:
    """A workspace without ``apps`` has nothing to check."""
    assert app_configs(tmp_path / "python") == []


def test_no_installed_apps_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The shipped repository has no app, and the lint step is green."""
    python_dir = tmp_path / "python"
    (python_dir / "apps").mkdir(parents=True)

    assert lint_installed_apps(python_dir) == 0
    assert capsys.readouterr().out == "No installed apps under python/apps. Nothing to lint.\n"
