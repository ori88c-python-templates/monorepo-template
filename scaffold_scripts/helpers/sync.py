"""Refresh the workspace lock after a registration change."""

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from helpers.errors import ScaffoldError

Sync = Callable[[Path], None]
Sort = Callable[[Path, Path], None]


def run_sync(python_dir: Path, sync: Sync | None) -> None:
    """Run ``sync``, or ``uv lock`` and ``uv sync`` when ``sync`` is omitted.

    Args:
        python_dir: Workspace directory the lock step runs in.
        sync: Replacement for the lock step. ``None`` runs uv.
    """
    if sync is None:
        lock_and_sync(python_dir)
        return
    sync(python_dir)


def lock_and_sync(python_dir: Path) -> None:
    """Run ``uv lock`` and ``uv sync --all-packages --all-groups``.

    Raises:
        ScaffoldError: ``uv`` is missing or either command exits non-zero.
    """
    uv = _uv()
    _run(python_dir, [uv, "lock"])
    _run(python_dir, [uv, "sync", "--all-packages", "--all-groups"])


def sort_imports(python_dir: Path, app_dir: Path) -> None:
    """Re-sort the import blocks of one installed app.

    A blueprint is sorted for the import package ``app``, which sorts before
    every shared package. The installed name may not, so the first-party
    block is re-sorted after the rename. Only the isort rule runs. Nothing
    else about the tree is rewritten.

    Args:
        python_dir: Workspace directory whose ruff config applies.
        app_dir: The installed app under ``python/apps``.
    """
    relative = app_dir.relative_to(python_dir).as_posix()
    _run(python_dir, [_uv(), "run", "ruff", "check", "--fix", "--select", "I", relative])


def _uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        message = "uv was not found on PATH."
        raise ScaffoldError(message)
    return uv


def _run(python_dir: Path, command: list[str]) -> None:
    try:
        subprocess.run(command, cwd=python_dir, check=True)  # noqa: S603
    except subprocess.CalledProcessError as exc:
        shown = " ".join(command[1:])
        message = f"uv {shown} failed with exit code {exc.returncode}."
        raise ScaffoldError(message) from exc
