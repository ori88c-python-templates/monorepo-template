---
name: add-app-category
description: >-
  Add a fourth app category to the monorepo: a new blueprint under
  python/_templates and the scaffold_scripts edits that teach add_app.py
  about it. Use when the user asks for a new app kind, a new template
  category, a worker or CLI or gRPC blueprint, or a new [tool.monorepo] type.
---

# Add an app category

A category is a blueprint directory under `python/_templates/<category>` plus the places in `scaffold_scripts/` that name it. CI discovers apps by directory and blueprints by `python/_templates/*/pyproject.toml`, so no workflow changes.

Start from the closest existing blueprint. `fastapi` for an HTTP server with a database, `fastmcp` for an HTTP server without one, `task_runner` for a process that runs once and exits.

## The blueprint

`add_app.py` copies the directory, then rewrites it. These are the parts it reads, so they must be present:

- The import package is `src/app`. The installed copy is renamed to the app name. Imports inside the tree are `from app.…` and `import app`.
- `src/app/config/app_consts.py` has `APP_NAME: Final = "<proof_name>"`. That proof name is the identity the blueprint speaks as (`^[a-z][a-z0-9_]*$`). Every occurrence of it, its hyphenated form, and its upper-case env prefix is replaced on install. Pick a name that does not collide with a real word in the tree.
- `pyproject.toml` has `[tool.monorepo] type = "<category>"`, `[project.scripts]` with one entry `app = "app.main:main"`, `[tool.uv.build-backend] module-name = "app"`, and shared packages as `{ path = "../../packages/<dir>" }` sources. Install turns those into `{ workspace = true }`.
- `[tool.importlinter]` has `root_package = "app"`, one `layers` contract with `exhaustive = true` and `containers = ["app"]` that names every top-level package under `src/app`, and one `forbidden` contract that keeps the framework out of `app.services` and `app.config`. Install rewrites `app` to the new import name. Shared packages have no contract.
- `README.md` contains a line that starts with `Shared packages supply`. Install replaces everything above it with the app's own opening.
- `Dockerfile` builds from `python/` with `COPY packages ./packages` and `COPY apps ./apps`, and ends in `CMD ["<proof-distribution>"]`. An HTTP category has `EXPOSE <port>`; install reads that port as the proof port. A category without a server has no `EXPOSE` line.
- `.cursor/rules/` holds only what this category does differently from the root rules.
- `tests/unit` always. `tests/integration` and `tests/e2e` only when they hold tests, because CI runs one job per existing directory.

Do not add `LICENSE`, `.dockerignore`, `.pre-commit-config.yaml`, or `.gitignore` to the blueprint. The repository root owns those.

## The scripts

- `scaffold_scripts/helpers/names.py`: add the constant, add it to `CATEGORIES`, extend the `_CATEGORY` regex, and update the `require_category` message.
- `scaffold_scripts/add_app.py`: add the category to the argparse `choices` and the description.
- `scaffold_scripts/helpers/copy_template.py`: add the display name to `_LABEL_BY_CATEGORY`. When the category has no server port, make `_proof_identity` return `port=None` for it, as it does for `TASK_RUNNER`.
- `scaffold_scripts/helpers/operations.py`: the two `category == TASK_RUNNER` checks decide whether a port is assigned. A second no-port category turns them into a membership test on a frozen set.
- `scaffold_scripts/helpers/env_example.py`: only when the category needs its own `.env.example` lines. An HTTP category already gets `<PREFIX>__SERVER__PORT`. A FastMCP-like category gets the MCP comments. A new comment block needs its own section header in `.env.example` and a branch here.
- Tests: one add, rename, and delete round trip in `scaffold_scripts/tests/test_commands.py`, and the env lines in `test_env_example.py`.

Then list the category in the Commands and Ports sections of `.cursor/skills/scaffold-scripts/SKILL.md` and in the root `README.md`.

## Verify

From `python/`, add one app, run its checks, and delete it:

```text
uv run python ../scaffold_scripts/add_app.py <category> smoke_<category>
uv run ruff check apps/smoke_<category>
uv run pyright apps/smoke_<category>
uv run lint-imports --config apps/smoke_<category>/pyproject.toml
uv run --directory apps/smoke_<category> pytest
uv run python ../scaffold_scripts/delete_app.py smoke_<category>
```

The Blueprints workflow runs the same steps for every category on each change under `python/_templates`, `python/packages`, or `scaffold_scripts`.
