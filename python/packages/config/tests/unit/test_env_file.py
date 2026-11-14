"""Repo-root discovery. The process working directory is not the env file location."""

from pathlib import Path

import pytest

from shared_config import load_redis_config, repo_root
from shared_config.loading import repo_root as loading_repo_root


def _markers(root: Path) -> None:
    """Create the two files ``repo_root`` searches for."""
    (root / "python").mkdir(parents=True)
    (root / "python" / "pyproject.toml").write_text("", encoding="utf-8")
    (root / "README.md").write_text("readme\n", encoding="utf-8")


def test_repo_root_is_the_checkout_that_contains_this_package() -> None:
    """Walking from the installed sources finds this repository."""
    root = repo_root()
    assert (root / "README.md").is_file()
    assert (root / "python" / "pyproject.toml").is_file()


def test_repo_root_ignores_the_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing cwd does not move the root."""
    found = repo_root()
    monkeypatch.chdir(tmp_path)
    assert repo_root() == found


def test_monorepo_root_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MONOREPO_ROOT is the explicit location when the package is not in the source tree."""
    root = tmp_path / "elsewhere"
    root.mkdir()
    monkeypatch.setenv("MONOREPO_ROOT", str(root))
    assert repo_root() == root.resolve()


def test_missing_markers_raise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Discovery fails with a named error when neither override nor markers exist."""
    monkeypatch.setattr(
        "shared_config.loading.__file__",
        str(tmp_path / "orphan" / "loading.py"),
    )
    with pytest.raises(FileNotFoundError, match="MONOREPO_ROOT"):
        loading_repo_root()


def test_loader_reads_the_root_file_not_the_cwd_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A .env next to the process is ignored. The root file is the one that counts."""
    root = tmp_path / "repo"
    _markers(root)
    (root / ".env").write_text("REDIS__HOST=from-root\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / ".env").write_text("REDIS__HOST=from-cwd\n", encoding="utf-8")
    monkeypatch.setenv("MONOREPO_ROOT", str(root))
    monkeypatch.chdir(elsewhere)
    assert load_redis_config().HOST == "from-root"


def test_explicit_none_ignores_the_root_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """env_file=None reads the process environment and skips every file."""
    root = tmp_path / "repo"
    _markers(root)
    (root / ".env").write_text("REDIS__HOST=from-root\n", encoding="utf-8")
    monkeypatch.setenv("MONOREPO_ROOT", str(root))
    monkeypatch.setenv("REDIS__HOST", "from-process")
    assert load_redis_config(env_file=None).HOST == "from-process"


def test_missing_explicit_env_file_is_an_error(tmp_path: Path) -> None:
    """A caller-supplied path that is not a file is a mistake, not an empty environment."""
    missing = tmp_path / "missing.env"
    with pytest.raises(FileNotFoundError):
        load_redis_config(env_file=missing)


def test_quoted_value_and_export_prefix(tmp_path: Path) -> None:
    """Quotes and an export prefix do not become part of the host name."""
    env_file = tmp_path / ".env"
    env_file.write_text('export REDIS__HOST="redis.internal"\n', encoding="utf-8")
    assert load_redis_config(env_file=env_file).HOST == "redis.internal"
