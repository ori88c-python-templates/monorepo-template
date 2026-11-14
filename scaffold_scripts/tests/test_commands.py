"""Add, rename, and delete against a copy of the real templates."""

import re
from pathlib import Path

from helpers.names import identifier_boundary, next_app_port
from helpers.operations import add_app, delete_app, rename_app
from helpers.paths import RepoPaths, read_text, write_text
from support import copied_repo, snapshot

_TEXT = {".py", ".md", ".toml", ".mdc", ".yaml", ".yml"}


def _noop(python_dir: Path) -> None:
    """Skip uv while still proving the command reached the lock step."""
    assert python_dir.name == "python"


def _expected_port(paths: RepoPaths) -> int:
    """Return the port the next HTTP app gets from the copied env and Compose files."""
    return next_app_port(read_text(paths.env_example), read_text(paths.compose_file))


def test_fastapi_add_rewrites_the_template_and_delete_restores_registration(tmp_path: Path) -> None:
    """A FastAPI app is wired through the workspace and the env example."""
    paths = copied_repo(tmp_path)
    before = snapshot(paths)
    port = _expected_port(paths)

    message = add_app(paths, "fastapi", "orders_api", sync=_noop)

    assert message == f"Added fastapi app 'orders_api' on port {port}."
    app = paths.app_dir("orders_api")
    main = read_text(app / "src" / "orders_api" / "main.py")
    assert 'loop="orders_api.main:make_selector_event_loop"' in main
    assert "from app." not in main
    _assert_tokens_absent(app, ("billing_api", "billing-api", "BILLING_API", "fastapi-template"))
    pyproject = read_text(app / "pyproject.toml")
    assert 'name = "orders-api"\n' in pyproject
    assert 'orders-api = "orders_api.main:main"\n' in pyproject
    assert 'module-name = "orders_api"\n' in pyproject
    assert 'type = "fastapi"\n' in pyproject
    assert 'root_package = "orders_api"\n' in pyproject
    assert 'containers = ["orders_api"]' in pyproject
    assert '"orders_api.services"' in pyproject
    assert 'root_package = "app"' not in pyproject
    assert '"app.' not in pyproject
    assert "{ workspace = true }" in pyproject
    assert "path =" not in pyproject
    readme = read_text(app / "README.md")
    assert readme.startswith(
        "# orders_api\n\nFastAPI app. Distribution `orders-api`. Import package `orders_api`.\n",
    )
    dockerfile = read_text(app / "Dockerfile")
    assert "COPY apps ./apps\n" in dockerfile
    assert "COPY apps/" not in dockerfile
    assert "--package orders-api" in dockerfile
    assert 'CMD ["orders-api"]' in dockerfile
    assert f"EXPOSE {port}\n" in dockerfile
    assert f"127.0.0.1:{port}" in dockerfile
    workspace = read_text(paths.workspace_pyproject)
    assert '"apps/orders_api"' in workspace
    assert 'root = "apps/orders_api"' in workspace
    assert read_text(paths.compose_file) == before["compose"]
    env = read_text(paths.env_example)
    assert f"ORDERS_API__SERVER__PORT={port}\n" in env
    assert "ORDERS_API__MCP__" not in env

    assert delete_app(paths, "orders_api", sync=_noop) == "Deleted app 'orders_api'."
    assert not app.exists()
    assert snapshot(paths) == before


def test_fastmcp_add_records_mcp_comments_and_leaves_compose(tmp_path: Path) -> None:
    """A FastMCP app records the MCP comment lines and does not edit Compose."""
    paths = copied_repo(tmp_path)
    before = read_text(paths.compose_file)
    port = _expected_port(paths)

    add_app(paths, "fastmcp", "shop_mcp", sync=_noop)

    assert read_text(paths.compose_file) == before
    env = read_text(paths.env_example)
    assert f"SHOP_MCP__SERVER__PORT={port}\n" in env
    assert "# SHOP_MCP__MCP__PATH=/mcp\n" in env
    assert "# SHOP_MCP__MCP__ENABLE_SSE_STREAM_RESPONSE=true\n" in env
    consts = read_text(paths.app_dir("shop_mcp") / "src" / "shop_mcp" / "config" / "app_consts.py")
    assert 'APP_NAME: Final = "shop_mcp"' in consts
    assert "notes_mcp" not in consts
    package = read_text(paths.app_dir("shop_mcp") / "src" / "shop_mcp" / "__init__.py")
    assert package == '"""shop_mcp application package."""\n'


def test_rename_keeps_the_assigned_port(tmp_path: Path) -> None:
    """Rename moves the tree and the registration without choosing a new port."""
    paths = copied_repo(tmp_path)
    port = _expected_port(paths)
    add_app(paths, "fastapi", "orders_api", sync=_noop)
    compose = read_text(paths.compose_file)

    message = rename_app(paths, "orders_api", "other_api", sync=_noop)

    assert message == "Renamed 'orders_api' to 'other_api'."
    assert not paths.app_dir("orders_api").exists()
    app = paths.app_dir("other_api")
    consts = read_text(app / "src" / "other_api" / "config" / "app_consts.py")
    assert 'APP_NAME: Final = "other_api"' in consts
    assert "ORDERS_API__SERVER__PORT" not in read_text(paths.env_example)
    assert f"OTHER_API__SERVER__PORT={port}\n" in read_text(paths.env_example)
    assert read_text(paths.compose_file) == compose
    workspace = read_text(paths.workspace_pyproject)
    assert "orders_api" not in workspace
    assert "orders-api" not in workspace
    assert '"apps/other_api"' in workspace
    assert "other-api" in workspace


def test_task_runner_add_assigns_no_port_and_rename_keeps_that(tmp_path: Path) -> None:
    """A task runner is registered without a server port and does not consume one."""
    paths = copied_repo(tmp_path)
    before = snapshot(paths)
    port = _expected_port(paths)

    message = add_app(paths, "task_runner", "nightly_export", sync=_noop)

    assert message == "Added task_runner app 'nightly_export'."
    app = paths.app_dir("nightly_export")
    assert 'type = "task_runner"\n' in read_text(app / "pyproject.toml")
    assert 'APP_NAME: Final = "nightly_export"' in read_text(
        app / "src" / "nightly_export" / "config" / "app_consts.py"
    )
    dockerfile = read_text(app / "Dockerfile")
    assert "EXPOSE " not in dockerfile
    assert "--package nightly-export" in dockerfile
    assert 'CMD ["nightly-export"]' in dockerfile
    env = read_text(paths.env_example)
    assert "NIGHTLY_EXPORT__SERVER__PORT" not in env
    assert "# NIGHTLY_EXPORT__GITHUB__ORG_URL=https://github.com/microsoft\n" in env
    assert not (app / "LICENSE").exists()
    assert read_text(paths.compose_file) == before["compose"]
    invariants = read_text(
        app / "tests" / "unit" / "config" / "app_config" / "test_production_invariants.py"
    )
    assert r"\nNIGHTLY_EXPORT__LOGGER__MIN_LOG_LEVEL=debug" in invariants
    assert "GITHUB_REPORT__LOGGER" not in invariants
    _assert_tokens_absent(app, ("GITHUB_REPORT__LOGGER__", "GITHUB_REPORT__GITHUB__"))
    _assert_symbols_absent(app, ("github_report", "github-report"))

    rename_app(paths, "nightly_export", "morning_export", sync=_noop)
    renamed_env = read_text(paths.env_example)
    assert "NIGHTLY_EXPORT__" not in renamed_env
    assert "MORNING_EXPORT__SERVER__PORT" not in renamed_env
    assert "# MORNING_EXPORT__GITHUB__REPOS_LIMIT=4\n" in renamed_env

    add_app(paths, "fastapi", "orders_api", sync=_noop)
    assert f"ORDERS_API__SERVER__PORT={port}\n" in read_text(paths.env_example)

    assert delete_app(paths, "morning_export", sync=_noop) == "Deleted app 'morning_export'."
    assert delete_app(paths, "orders_api", sync=_noop) == "Deleted app 'orders_api'."
    assert snapshot(paths) == before


def test_add_port_is_above_the_highest_compose_port(tmp_path: Path) -> None:
    """A port published only in Compose still reserves that number."""
    paths = copied_repo(tmp_path)
    reserved = _expected_port(paths) + 7
    write_text(
        paths.compose_file,
        read_text(paths.compose_file)
        + "\n  legacy-api:\n"
        + "    image: legacy-api\n"
        + "    environment:\n"
        + f'      LEGACY_API__SERVER__PORT: "{reserved}"\n',
    )
    compose = read_text(paths.compose_file)

    message = add_app(paths, "fastmcp", "shop_mcp", sync=_noop)

    assert message == f"Added fastmcp app 'shop_mcp' on port {reserved + 1}."
    assert f"SHOP_MCP__SERVER__PORT={reserved + 1}\n" in read_text(paths.env_example)
    assert read_text(paths.compose_file) == compose


def test_imports_are_sorted_after_the_lock_step_for_the_installed_app(tmp_path: Path) -> None:
    """Sorting needs the app installed, so it follows sync and targets that app's directory."""
    paths = copied_repo(tmp_path)
    calls: list[tuple[str, Path]] = []

    def record_sync(python_dir: Path) -> None:
        calls.append(("sync", python_dir))

    def record_sort(python_dir: Path, app_dir: Path) -> None:
        calls.append(("sort", app_dir))
        assert python_dir == paths.python_dir

    add_app(paths, "fastapi", "orders_api", sync=record_sync, sort=record_sort)
    rename_app(paths, "orders_api", "other_api", sync=record_sync, sort=record_sort)

    assert calls == [
        ("sync", paths.python_dir),
        ("sort", paths.app_dir("orders_api")),
        ("sync", paths.python_dir),
        ("sort", paths.app_dir("other_api")),
    ]


def test_first_apps_in_an_empty_workspace_use_the_section_headers(tmp_path: Path) -> None:
    """With no app line yet, the port and MCP comments go under their section headers."""
    paths = copied_repo(tmp_path)
    env = read_text(paths.env_example)
    env = "".join(
        line
        for line in env.splitlines(keepends=True)
        if "__SERVER__PORT=" not in line and "__MCP__" not in line and "__GITHUB" not in line
    )
    write_text(paths.env_example, env)
    write_text(paths.compose_file, "name: test\nservices:\n")

    first = add_app(paths, "fastapi", "orders_api", sync=_noop)
    second = add_app(paths, "fastmcp", "shop_mcp", sync=_noop)
    third = add_app(paths, "task_runner", "nightly_export", sync=_noop)

    assert first == "Added fastapi app 'orders_api' on port 8081."
    assert second == "Added fastmcp app 'shop_mcp' on port 8082."
    assert third == "Added task_runner app 'nightly_export'."
    updated = read_text(paths.env_example)
    server = updated.index("# --- Server (per app)")
    mcp = updated.index("# --- MCP (per app)")
    redis = updated.index("# --- Redis")
    orders_port = updated.index("ORDERS_API__SERVER__PORT=8081\n")
    assert server < orders_port < mcp
    assert orders_port < updated.index("SHOP_MCP__SERVER__PORT")
    assert mcp < updated.index("# SHOP_MCP__MCP__PATH=/mcp\n") < redis
    assert "# NIGHTLY_EXPORT__GITHUB__ORG_URL=https://github.com/microsoft\n" in updated


def _assert_tokens_absent(app: Path, tokens: tuple[str, ...]) -> None:
    for path, text in _text_files(app):
        for token in tokens:
            assert token not in text, path


def _assert_symbols_absent(app: Path, symbols: tuple[str, ...]) -> None:
    """Fail on a whole-token occurrence; ``github_report_config`` is not ``github_report``."""
    for path, text in _text_files(app):
        for symbol in symbols:
            pattern = rf"{identifier_boundary('-')}{re.escape(symbol)}(?![A-Za-z0-9_-])"
            assert re.search(pattern, text) is None, (path, symbol)


def _text_files(app: Path) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in app.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _TEXT and path.name != "Dockerfile":
            continue
        found.append((path, read_text(path)))
    return found
