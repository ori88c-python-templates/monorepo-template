"""A dependency-spec edit tests every member. A description edit does not."""

import pytest

from helpers.classify_changes import ProjectTexts, select
from helpers.errors import SelectionError
from helpers.workspace_graph import WorkspaceGraph

_PATH = "python/packages/alpha/pyproject.toml"
_OLD = """\
[project]
name = "alpha"
description = "before"
requires-python = ">=3.14"
dependencies = ["base"]

[tool.uv.sources]
base = { workspace = true }
"""


def test_dependency_spec_edit_selects_every_member(sample_graph: WorkspaceGraph) -> None:
    """Adding a dependency fills both lists with every member."""
    new = _OLD.replace('dependencies = ["base"]', 'dependencies = ["base", "solo"]')
    selection = select(sample_graph, [_PATH], {_PATH: ProjectTexts(_OLD, new)})
    assert selection.packages == ("alpha", "base", "beta", "solo")
    assert selection.apps == ("one", "two")


def test_description_edit_stays_on_the_normal_rule(sample_graph: WorkspaceGraph) -> None:
    """A description change still selects only ``alpha`` and its dependents."""
    new = _OLD.replace('description = "before"', 'description = "after"')
    selection = select(sample_graph, [_PATH], {_PATH: ProjectTexts(_OLD, new)})
    assert selection.packages == ("alpha", "beta")
    assert selection.apps == ("one", "two")


def test_member_pyproject_without_texts_is_rejected(sample_graph: WorkspaceGraph) -> None:
    """A member project file cannot be classified without both revisions."""
    with pytest.raises(SelectionError, match="No base and head text"):
        select(sample_graph, [_PATH])
