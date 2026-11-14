"""Blueprint and scaffold edits do not select a package or an app."""

import pytest

from helpers.classify_changes import select
from helpers.workspace_graph import WorkspaceGraph

_PATHS = (
    "python/_templates/fastapi/src/app/main.py",
    "scaffold_scripts/add_app.py",
)


@pytest.mark.parametrize("path", _PATHS)
def test_unrelated_path_selects_nothing(path: str, sample_graph: WorkspaceGraph) -> None:
    """The path is outside every workspace member."""
    selection = select(sample_graph, [path])
    assert selection.packages == ()
    assert selection.apps == ()
