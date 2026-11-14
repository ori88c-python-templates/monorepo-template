"""Workspace registration round trip."""

from helpers.names import AppIdentity
from helpers.paths import read_text
from helpers.workspace_toml import add_workspace_app, remove_workspace_app
from support import REPO

_ORDERS = AppIdentity(name="orders_api", category="fastapi", port=8083)


def test_workspace_add_and_remove_round_trip() -> None:
    """A new member can be removed without disturbing the other packages."""
    original = read_text(REPO / "python" / "pyproject.toml")

    added = add_workspace_app(original, _ORDERS)

    assert '"orders-api"' in added
    assert "orders-api = { workspace = true }\n" in added
    assert '"apps/orders_api"' in added
    assert '"apps/orders_api/src"' in added
    assert '"apps/orders_api/tests"' in added
    assert '"orders_api"' in added
    assert 'root = "apps/orders_api"\n' in added
    assert '"packages/config"' in added
    assert remove_workspace_app(added, _ORDERS) == original
