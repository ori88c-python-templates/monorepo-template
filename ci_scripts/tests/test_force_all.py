"""Workspace, lock, interpreter, workflow, and selector changes test every member."""

import pytest

from helpers.classify_changes import select
from helpers.workspace_graph import WorkspaceGraph

_PATHS = (
    "python/pyproject.toml",
    "python/uv.lock",
    "python/.python-version",
    ".github/workflows/tests.yml",
    "ci_scripts/select_affected.py",
)


@pytest.mark.parametrize("path", _PATHS)
def test_path_selects_every_member(path: str, sample_graph: WorkspaceGraph) -> None:
    """This path is not a single member, so both lists contain the whole workspace."""
    selection = select(sample_graph, [path])
    assert selection.packages == ("alpha", "base", "beta", "solo")
    assert selection.apps == ("one", "two")
