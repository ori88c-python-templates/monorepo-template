"""Directory names a workflow matrix is built from."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

Lister = Callable[[Path], list[str]]


def apps_with_dockerfile(python_dir: Path) -> list[str]:
    """Return installed app directories that have a ``Dockerfile``, sorted.

    Args:
        python_dir: The ``python/`` workspace directory.

    Returns:
        Directory names under ``python/apps``. An app without a Dockerfile
        is not an image and is left out. Blueprints are not included.
    """
    return _directories_with(python_dir / "apps", "Dockerfile")


def blueprint_categories(python_dir: Path) -> list[str]:
    """Return blueprint directories that have a ``pyproject.toml``, sorted.

    Args:
        python_dir: The ``python/`` workspace directory.

    Returns:
        Directory names under ``python/_templates``. Each is a category the
        add command accepts.
    """
    return _directories_with(python_dir / "_templates", "pyproject.toml")


def write_github_output_list(path: Path, name: str, values: list[str]) -> None:
    """Append ``name=<json list>`` for GitHub Actions.

    Args:
        path: The ``GITHUB_OUTPUT`` file. The line is appended.
        name: The output name.
        values: The list the workflow matrix reads.
    """
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={json.dumps(values)}\n")


def run_lister(
    *,
    prog: str,
    description: str,
    output_name: str,
    lister: Lister,
    argv: Sequence[str] | None,
) -> None:
    """Parse ``--repo-root`` and ``--github-output``, then print one JSON list.

    Args:
        prog: The command name argparse shows.
        description: The one-line help text.
        output_name: The ``GITHUB_OUTPUT`` key, such as ``apps``.
        lister: Reads the ``python/`` directory and returns the names.
        argv: CLI arguments. ``None`` reads the process arguments.
    """
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--github-output",
        type=Path,
        help=f"Append {output_name}=<json list> for GitHub Actions.",
    )
    args = parser.parse_args(argv)
    values = lister(args.repo_root / "python")
    if args.github_output is not None:
        write_github_output_list(args.github_output, output_name, values)
    sys.stdout.write(json.dumps(values) + "\n")


def _directories_with(root: Path, marker: str) -> list[str]:
    if not root.is_dir():
        return []
    directory_names_asc_by_name = sorted(
        child.name for child in root.iterdir() if (child / marker).is_file()
    )
    return directory_names_asc_by_name  # noqa: RET504
