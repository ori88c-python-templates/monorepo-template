"""Suite directories and the lines GitHub Actions reads."""

import json
from pathlib import Path

import pytest

from helpers.app_suites import suites_for_apps, write_github_output
from helpers.classify_changes import Selection
from select_affected import main


def test_missing_suite_directory_is_omitted(tmp_path: Path) -> None:
    """An app without ``tests/integration`` does not get that suite."""
    _suite(tmp_path, "billing_api", "unit")
    _suite(tmp_path, "billing_api", "integration")
    _suite(tmp_path, "billing_api", "e2e")
    _suite(tmp_path, "github_report", "unit")
    _suite(tmp_path, "github_report", "e2e")

    found = suites_for_apps(tmp_path, ("billing_api", "github_report"))

    assert [(item.app, item.suite) for item in found] == [
        ("billing_api", "unit"),
        ("billing_api", "integration"),
        ("billing_api", "e2e"),
        ("github_report", "unit"),
        ("github_report", "e2e"),
    ]


def test_github_output_is_two_json_lines(tmp_path: Path) -> None:
    """The workflow file gets one line per output, with no embedded newlines."""
    selection = Selection(packages=("config",), apps=("billing_api",))
    _suite(tmp_path, "billing_api", "unit")
    suites = suites_for_apps(tmp_path, selection.apps)
    output = tmp_path / "github_output"

    write_github_output(output, selection, suites)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0].removeprefix("packages=")) == ["config"]
    assert json.loads(lines[1].removeprefix("app_suites=")) == [
        {"app": "billing_api", "suite": "unit"},
    ]


def test_push_without_a_base_selects_every_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A push whose ``DIFF_BASE`` is missing or all zeros selects every member."""
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("DIFF_BASE", "0" * 40)
    _write_member(tmp_path, "packages/alpha", "alpha", ())
    _write_member(tmp_path, "apps/one", "one", ("alpha",))
    _suite(tmp_path, "one", "unit")
    _write_root(tmp_path, ("packages/alpha", "apps/one"))
    output = tmp_path / "github_output"

    main(["--repo-root", str(tmp_path), "--github-output", str(output)])

    assert json.loads(capsys.readouterr().out) == {"packages": ["alpha"], "apps": ["one"]}
    lines = output.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0].removeprefix("packages=")) == ["alpha"]
    assert json.loads(lines[1].removeprefix("app_suites=")) == [{"app": "one", "suite": "unit"}]


def test_push_with_a_base_does_not_select_every_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A push with a real ``DIFF_BASE`` diffs that SHA instead of selecting everyone."""
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("DIFF_BASE", "abc123def456")
    _write_member(tmp_path, "packages/alpha", "alpha", ())
    _write_member(tmp_path, "apps/one", "one", ("alpha",))
    _write_root(tmp_path, ("packages/alpha", "apps/one"))
    output = tmp_path / "github_output"

    with pytest.raises(SystemExit) as caught:
        main(["--repo-root", str(tmp_path), "--github-output", str(output)])

    assert caught.value.code == 1
    assert not output.exists()
    assert "git" in capsys.readouterr().err.lower()


def test_pull_request_without_base_sha_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A pull request with no base SHA fails before it reads the workspace."""
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.delenv("DIFF_BASE", raising=False)

    with pytest.raises(SystemExit) as caught:
        main(["--repo-root", str(tmp_path), "--github-output", str(tmp_path / "out")])

    assert caught.value.code == 1
    assert "DIFF_BASE" in capsys.readouterr().err


def _suite(root: Path, app: str, suite: str) -> None:
    (root / "python" / "apps" / app / "tests" / suite).mkdir(parents=True)


def _write_root(root: Path, members: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{member}"' for member in members)
    path = root / "python" / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"[tool.uv.workspace]\nmembers = [{listed}]\n", encoding="utf-8")


def _write_member(root: Path, member: str, name: str, dependencies: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{item}"' for item in dependencies)
    path = root / "python" / member / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\ndependencies = [{listed}]\n',
        encoding="utf-8",
    )
