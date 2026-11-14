"""Mark end-to-end tests. Logging fixtures come from ``shared_log_manager``."""

from pathlib import Path
from typing import Final

import pytest

_TESTS_ROOT: Final = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test under ``e2e/`` with that tree's name.

    Args:
        items: The collected session. Tests outside that tree are left unmarked.
    """
    for item in items:
        if not item.path.is_relative_to(_TESTS_ROOT):
            continue
        tree = item.path.relative_to(_TESTS_ROOT).parts[0]
        if tree == "e2e":
            item.add_marker(tree)
