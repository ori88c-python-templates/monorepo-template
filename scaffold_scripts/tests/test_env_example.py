"""Env-example lines for one app."""

import pytest

from helpers.env_example import add_app_env, remove_app_env, rename_app_env
from helpers.errors import ScaffoldError
from helpers.names import AppIdentity
from helpers.paths import read_text
from support import REPO

_ORDERS = AppIdentity(name="orders_api", category="fastapi", port=8083)
_SHOP = AppIdentity(name="shop_mcp", category="fastmcp", port=8084)
_OTHER = AppIdentity(name="other_api", category="fastapi", port=8083)
_NIGHTLY = AppIdentity(name="nightly_export", category="task_runner", port=None)
_RENAMED_NIGHTLY = AppIdentity(name="morning_export", category="task_runner", port=None)


def test_env_example_add_and_remove_round_trip() -> None:
    """FastAPI gains a port line. FastMCP also gains the MCP comments."""
    original = read_text(REPO / ".env.example")

    fastapi = add_app_env(original, _ORDERS)
    assert "ORDERS_API__SERVER__PORT=8083\n" in fastapi
    assert "ORDERS_API__MCP__" not in fastapi
    assert remove_app_env(fastapi, _ORDERS) == original

    fastmcp = add_app_env(original, _SHOP)
    assert "SHOP_MCP__SERVER__PORT=8084\n" in fastmcp
    assert "# SHOP_MCP__MCP__PATH=/mcp\n" in fastmcp
    assert "# SHOP_MCP__MCP__ENABLE_SSE_STREAM_RESPONSE=true\n" in fastmcp
    assert remove_app_env(fastmcp, _SHOP) == original

    task_runner = add_app_env(original, _NIGHTLY)
    assert "NIGHTLY_EXPORT__SERVER__PORT" not in task_runner
    assert "# NIGHTLY_EXPORT__GITHUB__ORG_URL=https://github.com/microsoft\n" in task_runner
    assert "# NIGHTLY_EXPORT__GITHUB__REPOS_LIMIT=4\n" in task_runner
    assert "# NIGHTLY_EXPORT__GITHUB__TOKEN=\n" in task_runner
    assert "# NIGHTLY_EXPORT__GITHUB__REQUEST_TIMEOUT_SECONDS=10\n" in task_runner
    assert "# NIGHTLY_EXPORT__GITHUB_REPORT__OUTPUT_DIR_PATH=github_reports\n" in task_runner
    assert remove_app_env(task_runner, _NIGHTLY) == original
    renamed = rename_app_env(task_runner, _NIGHTLY, _RENAMED_NIGHTLY)
    assert "NIGHTLY_EXPORT__" not in renamed
    assert "# MORNING_EXPORT__GITHUB__ORG_URL=https://github.com/microsoft\n" in renamed


def test_env_rename_keeps_the_port_value() -> None:
    """Renaming changes the prefix and leaves the number in place."""
    renamed = rename_app_env(
        add_app_env(read_text(REPO / ".env.example"), _ORDERS), _ORDERS, _OTHER
    )

    assert "OTHER_API__SERVER__PORT=8083\n" in renamed
    assert "ORDERS_API__SERVER__PORT" not in renamed


def test_empty_sections_take_the_line_after_their_header_comments() -> None:
    """A fresh workspace has headers and no app lines. The first app goes under them."""
    original = (
        "ENV=local\n"
        "\n"
        "# --- Server (per app) -----\n"
        "# PORT has no default.\n"
        "# HOST defaults to 0.0.0.0 when unset.\n"
        "\n"
        "# --- MCP (per app) -----\n"
        "# PATH defaults to /mcp.\n"
        "\n"
        "# --- Redis -----\n"
        "REDIS__HOST=127.0.0.1\n"
    )

    fastapi = add_app_env(original, _ORDERS)
    fastmcp = add_app_env(fastapi, _SHOP)

    assert fastapi == original.replace(
        "# HOST defaults to 0.0.0.0 when unset.\n",
        "# HOST defaults to 0.0.0.0 when unset.\nORDERS_API__SERVER__PORT=8083\n",
    )
    assert "ORDERS_API__SERVER__PORT=8083\nSHOP_MCP__SERVER__PORT=8084\n" in fastmcp
    assert (
        "# PATH defaults to /mcp.\n# SHOP_MCP__MCP__PATH=/mcp\n"
        "# SHOP_MCP__MCP__ENABLE_SSE_STREAM_RESPONSE=true\n\n# --- Redis"
    ) in fastmcp
    assert remove_app_env(remove_app_env(fastmcp, _SHOP), _ORDERS) == original


def test_a_header_with_no_comment_lines_takes_the_line_directly_under_it() -> None:
    """A section header followed by a blank line is still a valid anchor."""
    original = "# --- Server (per app) -----\n\n# --- Redis -----\nREDIS__HOST=127.0.0.1\n"

    added = add_app_env(original, _ORDERS)

    assert added == (
        "# --- Server (per app) -----\nORDERS_API__SERVER__PORT=8083\n\n"
        "# --- Redis -----\nREDIS__HOST=127.0.0.1\n"
    )


def test_missing_section_header_is_reported() -> None:
    """Without an app line or its header, the command stops before it writes."""
    with pytest.raises(ScaffoldError, match=r"no section that starts with '# --- Server"):
        add_app_env("ENV=local\n", _ORDERS)
