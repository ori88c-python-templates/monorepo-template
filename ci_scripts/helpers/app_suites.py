"""Test directories an affected app actually has."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from helpers.classify_changes import Selection

SUITES: Final = ("unit", "integration", "e2e")


@dataclass(frozen=True)
class AppSuite:
    """One existing ``tests/<suite>`` directory for one app."""

    app: str
    suite: str

    def to_json(self) -> dict[str, str]:
        """Return the object the workflow matrix reads."""
        return {"app": self.app, "suite": self.suite}


def suites_for_apps(repo_root: Path, apps: Sequence[str]) -> tuple[AppSuite, ...]:
    """Return suite directories that exist, apps in the given order.

    A suite is included only when ``python/apps/<app>/tests/<suite>`` is a
    directory. The order inside one app is unit, then integration, then e2e.

    Args:
        repo_root: Directory that contains ``python/apps``.
        apps: Affected app directory names.

    Returns:
        One entry per existing suite directory.
    """
    found: list[AppSuite] = []
    for app in apps:
        tests = repo_root / "python" / "apps" / app / "tests"
        for suite in SUITES:
            if (tests / suite).is_dir():
                found.append(AppSuite(app, suite))
    return tuple(found)


def write_github_output(path: Path, selection: Selection, suites: Sequence[AppSuite]) -> None:
    """Append ``packages`` and ``app_suites`` as single lines.

    GitHub Actions reads ``name=value`` from this file. Both values are JSON
    with no newlines.

    Args:
        path: The ``GITHUB_OUTPUT`` file. Lines are appended.
        selection: Packages and apps the change requires.
        suites: Suite directories for those apps.
    """
    package_line = "packages=" + json.dumps(list(selection.packages)) + "\n"
    suite_line = "app_suites=" + json.dumps([item.to_json() for item in suites]) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(package_line)
        handle.write(suite_line)
