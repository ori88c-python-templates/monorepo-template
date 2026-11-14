"""Temporary repositories for the scaffold tests."""

import shutil
from pathlib import Path

from helpers.paths import RepoPaths, ignore_skipped, read_text

REPO = Path(__file__).resolve().parents[2]


def bare_repo(tmp_path: Path) -> RepoPaths:
    """Return a repo with the expected files and no apps."""
    root = tmp_path / "repo"
    (root / "python" / "apps").mkdir(parents=True)
    (root / "compose.yaml").write_text("name: test\nservices:\n", encoding="utf-8", newline="\n")
    (root / ".env.example").write_text("", encoding="utf-8", newline="\n")
    (root / "python" / "pyproject.toml").write_text("", encoding="utf-8", newline="\n")
    return RepoPaths(root=root)


def copied_repo(tmp_path: Path) -> RepoPaths:
    """Return the real workspace files and templates, with an empty apps directory."""
    root = tmp_path / "repo"
    python = root / "python"
    python.mkdir(parents=True)
    (python / "apps").mkdir()
    shutil.copyfile(REPO / "compose.yaml", root / "compose.yaml")
    shutil.copyfile(REPO / ".env.example", root / ".env.example")
    shutil.copyfile(REPO / "python" / "pyproject.toml", python / "pyproject.toml")
    shutil.copytree(REPO / "python" / "_templates", python / "_templates", ignore=ignore_skipped)
    return RepoPaths(root=root)


def snapshot(paths: RepoPaths) -> dict[str, str]:
    """Return the three registration files the commands rewrite."""
    return {
        "workspace": read_text(paths.workspace_pyproject),
        "compose": read_text(paths.compose_file),
        "env": read_text(paths.env_example),
    }
