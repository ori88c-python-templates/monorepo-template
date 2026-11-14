# Scaffold scripts

Commands add, rename, and delete a Python app or a shared package. Run them from the repository root. They update the tree and `python/pyproject.toml`, and the app commands also update `.env.example`. Each command then runs `uv lock` and `uv sync --all-packages --all-groups`. Add and rename of an app also re-sort that app's import blocks with `ruff check --fix --select I`, because a blueprint is sorted for the package name `app` and the installed name may sort elsewhere.

App commands read `compose.yaml` only to choose a free port. They do not write it. After an app command succeeds, edit Compose as described in `.cursor/skills/scaffold-scripts/SKILL.md`. Package commands do not read `compose.yaml`.

An app name matches `^[a-z][a-z0-9_]*$`. `orders_api` is distribution `orders-api`, import package `orders_api`, and env prefix `ORDERS_API`.

## add_app.py

Arguments: `fastapi`, `fastmcp`, or `task_runner`, then the app name.

When `python/apps/<name>` already exists: `App '<name>' already exists at python/apps/<name>.`

Copies `python/_templates/<category>` into `python/apps/<name>` and registers the app in the workspace. FastAPI and FastMCP append `<PREFIX>__SERVER__PORT` to `.env.example`. FastMCP also gets the commented `<PREFIX>__MCP__*` lines. The port is one above the highest `<APP>__SERVER__PORT` in `.env.example` and `compose.yaml`, and at least `8081`. The success line reports it. A task runner appends commented `<PREFIX>__GITHUB__*` lines and `<PREFIX>__GITHUB_REPORT__OUTPUT_DIR_PATH`, and no server port. Its success line does not mention a port.

## rename_app.py

Arguments: source name, then target name.

When the source is missing: `App '<source>' does not exist.`
When the target exists: `App '<target>' already exists at python/apps/<target>.`

Renames the app directory, the import package, the workspace registration, and the env prefix. The category and the port stay.

## delete_app.py

Argument: the app name.

When the name is missing: `App '<name>' does not exist.`

Removes the app directory, its workspace registration, and its env lines. There is no confirmation prompt.

It does not edit `compose.yaml`. When that file still names the app (its Dockerfile path, its env prefix, or its service name), the success output gains a second line: `compose.yaml still references '<name>' on lines 44, 58, 67. Remove the service as the scaffold skill describes.` The exit code stays 0.

## add_package.py

Argument: the import name.

`shared_redis` is directory `python/packages/redis` and distribution `shared-redis`. A name without the `shared_` prefix, such as `github_client`, uses the import name as the directory. `shared_` alone is rejected.

When `python/packages/<dir>` already exists: `Package '<import>' already exists at python/packages/<dir>.`

When the import or distribution is already used: `Package '<import>' already exists.`

Creates an empty src-layout package and registers it in the workspace, including pytest `testpaths`. It does not write `.env.example`, `compose.yaml`, or Alembic.

## rename_package.py

Arguments: source import name, then target import name.

When the source is missing: `Package '<import>' does not exist.`

When the target directory exists: `Package '<import>' already exists at python/packages/<dir>.`

When the import or distribution is already used: `Package '<import>' already exists.`

Renames the directory, the import package, and the distribution name in Python files and `pyproject.toml` files under `python/`, including templates. The directory stays when only the `shared_` prefix changes.

## delete_package.py

Argument: the import name.

When the name is missing: `Package '<import>' does not exist.`

When an app, package, or template still requires it: `Package '<import>' is still required by <sorted names>.` Nothing is deleted. There is no confirmation prompt.

Removes the package directory and its workspace registration, including an Alembic path or a pyright execution environment under that directory.

## Example

In a fresh clone no app holds a port yet, so the first HTTP app gets `8081` and the next `8082`.

```text
uv run --directory python python ../scaffold_scripts/add_app.py fastapi orders_api
Added fastapi app 'orders_api' on port 8081.

uv run --directory python python ../scaffold_scripts/add_app.py fastmcp shop_mcp
Added fastmcp app 'shop_mcp' on port 8082.

uv run --directory python python ../scaffold_scripts/rename_app.py orders_api billing_portal
Renamed 'orders_api' to 'billing_portal'.

uv run --directory python python ../scaffold_scripts/delete_app.py shop_mcp
Deleted app 'shop_mcp'.

uv run --directory python python ../scaffold_scripts/add_package.py shared_widget
Added package 'shared_widget' at python/packages/widget.

uv run --directory python python ../scaffold_scripts/rename_package.py shared_widget shared_gadget
Renamed 'shared_widget' to 'shared_gadget'.

uv run --directory python python ../scaffold_scripts/delete_package.py shared_gadget
Deleted package 'shared_gadget'.
```

`billing_portal` keeps port `8081`. Update `compose.yaml` after each command that should appear in the local stack.

## Checks

From the repository root:

```text
uv run --directory python pytest ../scaffold_scripts/tests
uv run --directory scaffold_scripts --project ../python ruff check
uv run --directory scaffold_scripts --project ../python ruff format --check
uv run --directory scaffold_scripts --project ../python pyright
```

The tests use a temporary tree. They do not start Docker or run `uv sync`.
