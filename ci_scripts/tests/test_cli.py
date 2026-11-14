"""The CLI prints JSON and refuses a workspace it cannot read."""

import json
from pathlib import Path

import pytest

from select_affected import main


def test_all_prints_both_lists(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--all`` lists every package and every app in the temporary workspace."""
    _write_member(tmp_path, "packages/alpha", "alpha", ())
    _write_member(tmp_path, "apps/one", "one", ("alpha",))
    _write_root(tmp_path, ("packages/alpha", "apps/one"))
    main(["--repo-root", str(tmp_path), "--all"])
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"packages": ["alpha"], "apps": ["one"]}


def test_missing_project_name_exits(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A member without ``project.name`` is a hard failure, not an empty selection."""
    member = tmp_path / "python" / "packages" / "alpha"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text("[project]\nversion = '0.1.0'\n", encoding="utf-8")
    _write_root(tmp_path, ("packages/alpha",))
    with pytest.raises(SystemExit) as caught:
        main(["--repo-root", str(tmp_path), "--all"])
    assert caught.value.code == 1
    assert "project.name" in capsys.readouterr().err


def _write_root(root: Path, members: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{member}"' for member in members)
    text = f"""\
[tool.uv.workspace]
members = [{listed}]
"""
    path = root / "python" / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_member(root: Path, member: str, name: str, dependencies: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{item}"' for item in dependencies)
    text = f"""\
[project]
name = "{name}"
version = "0.1.0"
dependencies = [{listed}]
"""
    path = root / "python" / member / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
