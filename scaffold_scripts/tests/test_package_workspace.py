"""Workspace registration for one package."""

from helpers.package_names import identity_for_new_package
from helpers.package_workspace import add_workspace_package, remove_workspace_package
from helpers.paths import read_text
from support import REPO

_WIDGET = identity_for_new_package("shared_widget")


def test_workspace_add_and_remove_round_trip() -> None:
    """A new package can be removed without disturbing the other members."""
    original = read_text(REPO / "python" / "pyproject.toml")

    added = add_workspace_package(original, _WIDGET)

    assert '"shared-widget"' in added
    assert "shared-widget = { workspace = true }\n" in added
    assert '"packages/widget"' in added
    assert '"packages/widget/tests"' in added
    assert '"shared_widget"' in added
    assert '"packages/widget/tests/**/*.py"' in added
    assert 'root = "packages/widget"' not in added
    assert '"packages/config"' in added
    assert remove_workspace_package(added, _WIDGET) == original


def test_remove_drops_alembic_paths_and_execution_environments() -> None:
    """Delete cleans extras that add never creates."""
    original = read_text(REPO / "python" / "pyproject.toml")
    client = identity_for_new_package("github_client")
    database = identity_for_new_package("feature_flags_db")

    without_client = remove_workspace_package(original, client)
    without_database = remove_workspace_package(original, database)

    assert "packages/github_client" not in without_client
    assert 'root = "packages/github_client/tests"' not in without_client
    assert "packages/github_client/tests/fakes" not in without_client
    assert '"github_client"' not in without_client
    assert "packages/feature_flags_db/alembic" not in without_database
    assert "packages/feature_flags_db/alembic/versions/*.py" not in without_database
    assert '"packages/config"' in without_client
    assert '"packages/config"' in without_database
