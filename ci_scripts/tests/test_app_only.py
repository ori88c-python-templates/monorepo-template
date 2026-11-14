"""An app change does not select the packages that app depends on."""

from helpers.classify_changes import select
from helpers.workspace_graph import WorkspaceGraph


def test_app_change_does_not_select_its_dependencies(sample_graph: WorkspaceGraph) -> None:
    """Changing ``one`` tests ``one`` and does not test ``beta`` or ``alpha``."""
    selection = select(sample_graph, ["python/apps/one/src/one/main.py"])
    assert selection.packages == ()
    assert selection.apps == ("one",)
