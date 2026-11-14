"""A rename contributes both the old path and the new path."""

from helpers.classify_changes import paths_from_name_status, select
from helpers.workspace_graph import WorkspaceGraph


def test_rename_counts_both_paths(sample_graph: WorkspaceGraph) -> None:
    """Moving a file from ``one`` to ``two`` selects both apps."""
    text = "R100\tpython/apps/one/old.py\tpython/apps/two/new.py\n"
    selection = select(sample_graph, paths_from_name_status(text))
    assert selection.packages == ()
    assert selection.apps == ("one", "two")
