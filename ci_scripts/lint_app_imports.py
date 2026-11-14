"""Run import-linter for every installed app."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def app_configs(python_dir: Path) -> list[Path]:
    """Return each installed app's ``pyproject.toml``, sorted by directory name.

    Args:
        python_dir: The ``python/`` workspace directory.

    Returns:
        Config files under ``python/apps``. Templates are not included.
    """
    apps = python_dir / "apps"
    if not apps.is_dir():
        return []
    configs_asc_by_directory = sorted(
        path for path in apps.glob("*/pyproject.toml") if path.is_file()
    )
    return configs_asc_by_directory  # noqa: RET504


def lint_installed_apps(python_dir: Path) -> int:
    """Check every installed app contract and stop at the first failure.

    A workspace with no installed app has nothing to check and passes. The
    blueprints under ``_templates`` are not linted here.

    Args:
        python_dir: The ``python/`` workspace directory.

    Returns:
        The exit code: ``0`` when every contract is kept or no app exists,
        otherwise the first failing ``lint-imports`` exit code.
    """
    configs_asc_by_directory = app_configs(python_dir)
    if not configs_asc_by_directory:
        sys.stdout.write("No installed apps under python/apps. Nothing to lint.\n")
        return 0
    uv = shutil.which("uv")
    if uv is None:
        sys.stderr.write("uv was not found on PATH.\n")
        return 1
    for config in configs_asc_by_directory:
        relative = config.relative_to(python_dir).as_posix()
        result = subprocess.run(  # noqa: S603
            [uv, "run", "lint-imports", "--config", relative],
            cwd=python_dir,
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
    return 0


def main() -> None:
    """Lint the apps under this repository's ``python/apps``."""
    python_dir = Path(__file__).resolve().parents[1] / "python"
    raise SystemExit(lint_installed_apps(python_dir))


if __name__ == "__main__":
    main()
