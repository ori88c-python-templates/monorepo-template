"""Print the packages and apps whose tests a change requires."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from helpers.app_suites import suites_for_apps, write_github_output
from helpers.classify_changes import (
    ProjectTexts,
    Selection,
    every_member,
    is_member_project_file,
    paths_from_name_status,
    select,
)
from helpers.errors import SelectionError
from helpers.workspace_graph import WorkspaceGraph, load_graph


def main(argv: Sequence[str] | None = None) -> None:
    """Print the affected packages and apps as one JSON object.

    Args:
        argv: CLI arguments. ``None`` reads the process arguments.
    """
    parser = argparse.ArgumentParser(
        prog="select_affected.py",
        description="Print the packages and apps a git change requires tests for.",
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Append packages and app_suites for GitHub Actions.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Select every workspace member.")
    group.add_argument("--base", help="Diff this revision against HEAD.")
    args = parser.parse_args(argv)
    try:
        select_all, base = _selection_mode(args.all, args.base, github_output=args.github_output)
        graph = load_graph(args.repo_root / "python")
        chosen = _choose(args.repo_root, graph, select_all=select_all, base=base)
        if args.github_output is not None:
            suites = suites_for_apps(args.repo_root, chosen.apps)
            write_github_output(args.github_output, chosen, suites)
    except SelectionError as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from exc
    sys.stdout.write(json.dumps(chosen.to_json(), indent=2) + "\n")


def _selection_mode(
    select_all: bool,
    base: str | None,
    *,
    github_output: Path | None,
) -> tuple[bool, str | None]:
    """Return whether to select every member, and the diff base when not.

    ``--all`` and ``--base`` win. ``--github-output`` alone reads ``DIFF_BASE``.
    An empty value or an all-zero SHA selects every member, except a pull
    request with no base, which fails.

    Raises:
        SelectionError: No mode was given, or a pull request has no base SHA.
    """
    if select_all:
        return True, None
    if base is not None:
        return False, base
    if github_output is not None:
        return _mode_from_github_env()
    raise SelectionError("Pass --all, --base, or --github-output.")


def _mode_from_github_env() -> tuple[bool, str | None]:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base = os.environ.get("DIFF_BASE", "").strip()
    if base and set(base) != {"0"}:
        return False, base
    if event == "pull_request":
        raise SelectionError("DIFF_BASE is required for a pull request.")
    return True, None


def _choose(
    repo_root: Path,
    graph: WorkspaceGraph,
    *,
    select_all: bool,
    base: str | None,
) -> Selection:
    if select_all:
        return every_member(graph)
    if base is None:
        raise SelectionError("Pass --all or --base.")
    status = _git_name_status(repo_root, base)
    paths = paths_from_name_status(status)
    project_texts_by_path = _pyproject_texts(repo_root, base, paths)
    return select(graph, paths, project_texts_by_path)


def _git_name_status(repo_root: Path, base: str) -> str:
    result = _git(repo_root, "diff", "--name-status", "-M", f"{base}...HEAD")
    if result.returncode != 0:
        detail = result.stderr.strip() or "git diff failed."
        raise SelectionError(detail)
    return result.stdout


def _pyproject_texts(
    repo_root: Path,
    base: str,
    paths: Sequence[str],
) -> Mapping[str, ProjectTexts]:
    """Read the base and HEAD text of each changed member ``pyproject.toml``.

    Other paths are ignored. A missing blob is ``None``, which means the file
    was added or deleted in that revision.

    Args:
        repo_root: Directory that contains ``.git``.
        base: The revision ``select`` diffs against HEAD.
        paths: Repo-relative paths from ``git diff --name-status``.

    Returns:
        One ``ProjectTexts`` per changed member project file.
    """
    project_texts_by_path: dict[str, ProjectTexts] = {}
    for path in paths:
        if not is_member_project_file(path):
            continue
        project_texts_by_path[path] = ProjectTexts(
            _blob(repo_root, base, path),
            _blob(repo_root, "HEAD", path),
        )
    return project_texts_by_path


def _blob(repo_root: Path, revision: str, path: str) -> str | None:
    result = _git(repo_root, "show", f"{revision}:{path}")
    if result.returncode != 0:
        return None
    return result.stdout


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if git is None:
        raise SelectionError("git was not found on PATH.")
    return subprocess.run(  # noqa: S603
        [git, *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    main()
