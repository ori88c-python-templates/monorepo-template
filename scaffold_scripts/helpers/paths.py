"""Locations the scaffold commands read and write."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from helpers.errors import ScaffoldError

SKIPPED_DIRS: Final = frozenset(
    {"__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache", ".venv"},
)


@dataclass(frozen=True)
class RepoPaths:
    """The repository files one app registration touches."""

    root: Path

    @classmethod
    def discover(cls) -> RepoPaths:
        """Return the repo that contains this helpers package.

        Raises:
            ScaffoldError: ``compose.yaml`` is not where the layout says it is.
        """
        root = Path(__file__).resolve().parents[2]
        if not (root / "compose.yaml").is_file():
            message = f"Repository root not found from {Path(__file__).resolve()}."
            raise ScaffoldError(message)
        return cls(root=root)

    @property
    def python_dir(self) -> Path:
        """Return the uv workspace directory."""
        return self.root / "python"

    @property
    def apps_dir(self) -> Path:
        """Return ``python/apps``."""
        return self.python_dir / "apps"

    @property
    def workspace_pyproject(self) -> Path:
        """Return the workspace ``pyproject.toml``."""
        return self.python_dir / "pyproject.toml"

    @property
    def compose_file(self) -> Path:
        """Return the root Compose file."""
        return self.root / "compose.yaml"

    @property
    def env_example(self) -> Path:
        """Return the committed env example."""
        return self.root / ".env.example"

    def app_dir(self, name: str) -> Path:
        """Return ``python/apps/<name>``."""
        return self.apps_dir / name

    @property
    def packages_dir(self) -> Path:
        """Return ``python/packages``."""
        return self.python_dir / "packages"

    def package_dir(self, directory: str) -> Path:
        """Return ``python/packages/<directory>``."""
        return self.packages_dir / directory

    def template_dir(self, category: str) -> Path:
        """Return ``python/_templates/<category>``."""
        return self.python_dir / "_templates" / category


def read_text(path: Path) -> str:
    """Read ``path`` as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write ``path`` as UTF-8 with LF line endings."""
    path.write_text(text, encoding="utf-8", newline="\n")


def iter_files(root: Path) -> list[Path]:
    """Return every file under ``root``, skipping tool and cache directories.

    Args:
        root: Directory to walk. A missing directory yields no files.

    Returns:
        Files in directory-walk order. Nothing under a ``SKIPPED_DIRS``
        directory is included.
    """
    if not root.is_dir():
        return []
    files: list[Path] = []
    for child in root.iterdir():
        if child.is_dir():
            if child.name in SKIPPED_DIRS:
                continue
            files.extend(iter_files(child))
        elif child.is_file():
            files.append(child)
    return files


def ignore_skipped(_directory: str, names: list[str]) -> set[str]:
    """Return the ``copytree`` ignore set for ``SKIPPED_DIRS``."""
    return {name for name in names if name in SKIPPED_DIRS}
