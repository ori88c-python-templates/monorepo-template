---
name: scaffold-scripts
description: >-
  Add, rename, and delete Python apps and shared packages with
  scaffold_scripts/add_app.py, rename_app.py, delete_app.py, add_package.py,
  rename_package.py, and delete_package.py. Use when the user asks to add,
  create, rename, or delete a FastAPI, FastMCP, or task-runner app, or a
  shared package, or to change an app directory, Compose service, workspace
  member, server port, or package directory.
---

# Scaffold scripts

Cookiecutter is not used. Run the commands below from the repository root. App commands update the app directory, `python/pyproject.toml`, and `.env.example`. Package commands update the package directory and `python/pyproject.toml`. Both then run `uv lock` and `uv sync --all-packages --all-groups`. Do not hand-edit those lists when a command can do it. App commands read `compose.yaml` only to choose a free port. After an app command succeeds, edit `compose.yaml` as described below. Do not leave that file for the script. Package commands do not read it.

Images copy every app with `COPY apps ./apps`. Add, rename, and delete do not edit Dockerfiles of other apps.

## Commands

```text
uv run --directory python python ../scaffold_scripts/add_app.py fastapi my_api
uv run --directory python python ../scaffold_scripts/add_app.py fastmcp my_mcp
uv run --directory python python ../scaffold_scripts/add_app.py task_runner my_task
uv run --directory python python ../scaffold_scripts/rename_app.py my_api other_api
uv run --directory python python ../scaffold_scripts/delete_app.py my_api
```

Arguments are positional. `fastapi`, `fastmcp`, and `task_runner` are the template categories. The category is stored as `[tool.monorepo] type` in the app `pyproject.toml`. A new category is `.cursor/skills/add-app-category/SKILL.md`.

## Fail fast

The command checks its arguments before it writes, then exits with one of these sentences:

- Add, when `python/apps/<name>` exists: `App '<name>' already exists at python/apps/<name>.`
- Rename, when the source is missing: `App '<source>' does not exist.`
- Rename, when the target exists: `App '<target>' already exists at python/apps/<target>.`
- Delete, when the name is missing: `App '<name>' does not exist.`

An app name matches `^[a-z][a-z0-9_]*$`. `orders_api` is distribution `orders-api`, import package `orders_api`, and env prefix `ORDERS_API`.

## Ports

Add assigns the next integer above the highest `<APP>__SERVER__PORT` in `.env.example` and `compose.yaml`, and at least `8081`, for `fastapi` and `fastmcp`. The success line reports that port. A `task_runner` gets no port. Its success line does not mention one, and it does not consume a number the next HTTP app would have used. Rename keeps the category and, for an HTTP app, that port. Delete removes the app immediately. There is no confirmation flag.

FastMCP also gets commented `<PREFIX>__MCP__*` lines in `.env.example`. A task runner gets commented `<PREFIX>__GITHUB__*` lines and `<PREFIX>__GITHUB_REPORT__OUTPUT_DIR_PATH`, and no `<PREFIX>__SERVER__PORT`.

## Compose

Edit `compose.yaml` after the command succeeds. Use the port from the success line when the app has one.

A task runner is not part of `docker compose up`. Add its service with `profiles: ["<distribution-name>"]`, no `ports`, and no healthcheck. Document:

```text
docker compose --profile <distribution-name> run --build --rm <distribution-name>
```

It still sets `MONOREPO_ROOT=/app`. It waits for Redis or a migrate service only when that app actually uses them. A task runner that only calls an external API does not.

Add an HTTP app service named with the distribution name (`orders_api` becomes `orders-api`):

- `dockerfile: apps/<name>/Dockerfile`
- publish `127.0.0.1:<port>:<port>`
- `REDIS__HOST=redis`
- `<PREFIX>__SERVER__PORT` set to the printed port
- `MONOREPO_ROOT=/app`

A FastAPI app that uses Postgres also sets `POSTGRES__HOST=postgres` and waits until each logical database it uses has been migrated. A FastMCP app waits for healthy Redis only.

One migrate service per logical database. Add one only when the new app uses a database that does not have one yet. The package, the image `COPY` lines, and the Alembic command are `.cursor/skills/alembic/SKILL.md`.

Rename the app service, its Dockerfile path, and its env prefix. Keep the port. Point a migrate service at the new Dockerfile only when that service was built from the renamed app.

Delete removes the app service. Remove a migrate service only when no remaining app uses that logical database. Leave Redis, Postgres, and unrelated migrate services. When `delete_app.py` prints a second line naming Compose line numbers, those are the lines to edit; the command never edits them itself.

The workflows discover apps by directory. Add and delete need no CI edit.

## Workspace

Registration adds the workspace member, the root dependency, `[tool.uv.sources]`, ruff `src`, `known-first-party`, per-file-ignores, pyright `include`, `extraPaths` for `src` only, and one `executionEnvironments` entry whose extra paths are `apps/<name>` and `apps/<name>/src`. Root pytest `testpaths` stay the shared packages. Run an app's tests with `uv run --directory python/apps/<name> pytest`.

The blueprint under `python/_templates/<category>` keeps the import package `app`. The installed copy renames it. These commands add, rename, or delete an app. They do not refresh an existing app from its template. Deleting an app and adding it again assigns a new port.

## Packages

```text
uv run --directory python python ../scaffold_scripts/add_package.py shared_widget
uv run --directory python python ../scaffold_scripts/rename_package.py shared_widget shared_gadget
uv run --directory python python ../scaffold_scripts/delete_package.py shared_widget
```

The argument is the import name. It matches `^[a-z][a-z0-9_]*$`. A leading `shared_` is stripped once for the directory: `shared_redis` lives in `python/packages/redis`, and its distribution name is `shared-redis`. `github_client` and `feature_flags_db` keep the import name as the directory. Rename and delete find an existing package by `[tool.uv.build-backend] module-name`.

Add writes an empty src-layout package: `pyproject.toml` with no dependencies, `src/<import>/__init__.py`, `py.typed`, `tests/<import>/test_import.py`, and a one-line README. `tests/` has no `__init__.py`. It does not write library code, Alembic, `.env.example`, or `compose.yaml`.

The command exits before it writes when:

- Add, and `python/packages/<dir>` exists: `Package '<import>' already exists at python/packages/<dir>.`
- Add, and the import or distribution is already used: `Package '<import>' already exists.`
- Rename or delete, and no package has that module name: `Package '<import>' does not exist.`
- Rename, and the target directory exists: `Package '<import>' already exists at python/packages/<dir>.`
- Rename, and the import or distribution is already used: `Package '<import>' already exists.`
- Delete, and something still requires it: `Package '<import>' is still required by <sorted names>.`

Those names are workspace directory names (`orders_api`, `prometheus`) and template categories (`template fastapi`). There is no confirmation flag. Nothing is deleted.

Registration adds the workspace member, the root dependency, `[tool.uv.sources]`, pytest `testpaths`, ruff `src` for `src` and `tests`, `known-first-party`, the shared test ignore, pyright `include` for `src` and `tests`, and `extraPaths` for `src` only. It does not add an execution environment, an Alembic path, `N802`, `S105`, `S106`, or a pytest `pythonpath` entry. Add those only when the new library needs them. Import-linter stays an app contract. A package has no layer stack.

Rename rewrites `python/**/*.py`, every `pyproject.toml` under `python/` (including templates), and the package README. The directory stays put when only the `shared_` prefix changes. It does not edit `compose.yaml`, `.env.example`, or `.cursor/`.

After add, write the library and decide which apps depend on it. For a database package, follow `.cursor/skills/alembic/SKILL.md`. The logical key is not a function of the directory.

After rename, update Compose, the env inventory, and prose when those files name the old package.

After delete, remove a migrate service and an inventory line only when no remaining package uses that logical database.
