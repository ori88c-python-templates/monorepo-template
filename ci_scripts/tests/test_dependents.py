"""A changed package selects its dependents, not its dependencies."""

from helpers.classify_changes import select
from helpers.workspace_graph import WorkspaceGraph


def test_reverse_bfs_includes_transitive_and_direct_apps(sample_graph: WorkspaceGraph) -> None:
    """``alpha`` selects ``beta`` and both apps, and leaves ``base`` and ``solo`` out."""
    selection = select(sample_graph, ["python/packages/alpha/src/alpha.py"])
    assert selection.packages == ("alpha", "beta")
    assert selection.apps == ("one", "two")
