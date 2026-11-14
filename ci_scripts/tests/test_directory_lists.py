"""App image and blueprint discovery for workflow matrices."""

import json
from pathlib import Path

import pytest

from helpers.directory_lists import apps_with_dockerfile, blueprint_categories
from list_app_images import main as images_main
from list_blueprints import main as blueprints_main


def test_apps_with_dockerfile_are_sorted_and_skip_apps_without_one(tmp_path: Path) -> None:
    """Only an app directory that holds a Dockerfile is an image."""
    python_dir = tmp_path / "python"
    for name in ("shop_mcp", "orders_api"):
        app = python_dir / "apps" / name
        app.mkdir(parents=True)
        (app / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (python_dir / "apps" / "no_image").mkdir()
    (python_dir / "apps" / "stray.txt").write_text("", encoding="utf-8")

    assert apps_with_dockerfile(python_dir) == ["orders_api", "shop_mcp"]


def test_empty_or_missing_apps_directory_lists_nothing(tmp_path: Path) -> None:
    """The shipped repository has no app, and the image job is skipped."""
    python_dir = tmp_path / "python"
    assert apps_with_dockerfile(python_dir) == []
    (python_dir / "apps").mkdir(parents=True)
    assert apps_with_dockerfile(python_dir) == []


def test_blueprint_categories_need_a_pyproject(tmp_path: Path) -> None:
    """A blueprint directory without ``pyproject.toml`` is not a category."""
    templates = tmp_path / "python" / "_templates"
    for name in ("task_runner", "fastapi"):
        (templates / name).mkdir(parents=True)
        (templates / name / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (templates / "draft").mkdir()

    assert blueprint_categories(tmp_path / "python") == ["fastapi", "task_runner"]
    assert blueprint_categories(tmp_path / "elsewhere") == []


def test_commands_print_json_and_append_github_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both commands print one JSON list and append one ``name=`` line."""
    python_dir = tmp_path / "python"
    (python_dir / "apps" / "orders_api").mkdir(parents=True)
    (python_dir / "apps" / "orders_api" / "Dockerfile").write_text("FROM scratch\n")
    (python_dir / "_templates" / "fastapi").mkdir(parents=True)
    (python_dir / "_templates" / "fastapi" / "pyproject.toml").write_text("[project]\n")
    output = tmp_path / "github_output"

    images_main(["--repo-root", str(tmp_path), "--github-output", str(output)])
    assert json.loads(capsys.readouterr().out) == ["orders_api"]
    blueprints_main(["--repo-root", str(tmp_path), "--github-output", str(output)])
    assert json.loads(capsys.readouterr().out) == ["fastapi"]

    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines == ['apps=["orders_api"]', 'categories=["fastapi"]']
