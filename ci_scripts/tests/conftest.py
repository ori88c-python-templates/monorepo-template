"""Put ``ci_scripts`` on the import path and share the sample graph."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from helpers.workspace_graph import WorkspaceGraph  # noqa: E402


@pytest.fixture
def sample_graph() -> WorkspaceGraph:
    """Return a graph with a dependency chain and one unconnected package.

    ``alpha`` depends on ``base``. ``beta`` depends on ``alpha``. ``one`` depends
    on ``beta``. ``two`` depends on ``alpha``. ``solo`` depends on nobody.
    """
    return WorkspaceGraph(
        packages=frozenset({"alpha", "base", "beta", "solo"}),
        apps=frozenset({"one", "two"}),
        dependency_names_by_member={
            "base": frozenset(),
            "alpha": frozenset({"base"}),
            "beta": frozenset({"alpha"}),
            "solo": frozenset(),
            "one": frozenset({"beta"}),
            "two": frozenset({"alpha"}),
        },
    )
