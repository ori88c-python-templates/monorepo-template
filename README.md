# Python Monorepo Template

[![Tests](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/tests.yml/badge.svg)](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/tests.yml)
[![Lint](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/lint.yml/badge.svg)](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/lint.yml)
[![Blueprints](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/blueprints.yml/badge.svg)](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/blueprints.yml)
[![Image](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/image.yml/badge.svg)](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/image.yml)
[![Audit](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/audit.yml/badge.svg)](https://github.com/ori88c-python-templates/monorepo-template/actions/workflows/audit.yml)

Production-grade Python monorepo template where every app, whatever its kind, is built around **dependency injection** and **zero global state**. Each app has one composition root (`LifecycleManager`) that wires clients, services, and loggers, so tests inject dependencies instead of monkeypatching in retrospect, which boosts predictability and avoids undesired side effects.

Shared infrastructure lives once in shared packages: reusable components such as `LogManager`, a database schema more than one app can use (`feature_flags_db`), and `RedisClient`.

Three blueprints ship, descended from the [FastAPI](https://github.com/ori88c-python-templates/fastapi-polyrepo-template), [FastMCP](https://github.com/ori88c-python-templates/fastmcp-polyrepo-template), and [task runner](https://github.com/ori88c-python-templates/task-runner-template) polyrepo templates; scaffold scripts stamp them out, AI rules and skills (for Claude, Cursor, Codex, and other AI-assisted IDEs) keep the conventions, and CI runs only the tests a change affects.

## Table of Contents

- [Highlights](#highlights)
- [Why this template](#why-this-template)
- [Architecture](#architecture)
- [Shared packages](#shared-packages)
- [Layout](#layout)
- [Working with the monorepo](#working-with-the-monorepo)
- [Running](#running)
- [Configuration](#configuration)
- [Logging](#logging)
- [Schema migrations](#schema-migrations)
- [Container images](#container-images)
- [Testing](#testing)
- [Linting and type checking](#linting-and-type-checking)
- [Pre-commit hooks](#pre-commit-hooks)
- [CI](#ci)
- [AI rules and skills](#ai-rules-and-skills)
- [Adding an app category](#adding-an-app-category)
- [Not shipped](#not-shipped)
- [License](#license)

## Highlights

- **Dependency injection, zero global state, in every category** 🧩: Every component takes dependencies in `__init__`; each app's `LifecycleManager` (the composition root) constructs the clients, services, and loggers and wires them. `main.py` only builds `AppConfig` and that manager. No module-level config, logger, or client anywhere in the tree.
- **Three-layer import DAG, enforced per app** 🧭: Protocol surface (HTTP via FastAPI, MCP via FastMCP), services (`FeatureFlagService`, `UserNotesService`), and injected clients (`PostgresClient`, `GithubClient`) stay loosely coupled so a service is tested without the framework and a client without a route. Each app carries an [import-linter](https://import-linter.readthedocs.io/) contract; the lint workflow runs it for every installed app.
- **Shared packages instead of copies** 📦: Config loaders, structured logging, middleware, Redis, Postgres, Prometheus, and the installed-version helper are written once under `python/packages/`. An app imports them and keeps only its own business logic.
- **Blueprints plus scaffold scripts** 🏗️: `python/_templates/` holds one blueprint per category. You can add a blueprint of your own, such as an Airflow blueprint. `scaffold_scripts/` adds, renames, and deletes apps and packages, registers them in the workspace, and runs `uv lock`. No cookiecutter.
- **Smart tests CI** 🎯: The Tests workflow reads the workspace dependency graph and runs only the packages and apps a change affects. A package change selects that package and everything that depends on it; an app change selects that app only. Each app suite (unit, integration, e2e) is its own job, so durations are visible.
- **Blueprints tested in CI** 🧱: On every change to a blueprint, a shared package, or the scaffold scripts, the Blueprints workflow scaffolds a fresh app from each category and runs ruff (check and format), pyright, lint-imports, and the app's pytest suites against it.
- **One `.env`, one lock, one venv, one Compose stack** 🔗: A single uv workspace under `python/`, one `.env` at the repository root with per-app prefixes, and one `compose.yaml` that starts Redis and Postgres. HTTP apps and migrate services are added after `add_app.py`.
- **AI rules and skills that keep the conventions** 🤖: Root rules cover every Python file; blueprint rules cover what one category does differently. Skills document the scaffold scripts, Alembic, client packages, and adding a new template category, so AI-assisted edits copy this architecture instead of inventing one.
- **Production-shaped ops** 🚢: Non-root multi-stage images built from one context, Kubernetes probes and a Prometheus scrape on HTTP apps, Alembic out of band, and a task-runner shape for jobs.
- **Supply-chain hygiene** 🔒: SHA-pinned Actions, weekly Dependabot for the `uv` lockfile and GitHub Actions, and a `uv audit` workflow on push, pull request, and a weekly schedule.

## Why this template

Python does not prescribe an architecture, and a monorepo multiplies whatever architecture the first app had. Without shared conventions, **tightly coupled components, module-level globals, and copied infrastructure are common in Python codebases**: the third app that talks to Redis declares a third Redis config model, and the fourth copies the one with the bug. The risk is sharper in AI-assisted development, where each existing pattern becomes the baseline the next change copies.

This template fixes both sides. Blueprints give every new app the same starting architecture, and shared packages give every app the same infrastructure, so the differences between two apps are the differences in their product code.

The guiding constraint is the one the polyrepos established: nothing important is reachable through a module-level global. No global config object, no global logger, no import-time singletons. Every component declares what it needs in its `__init__`, and a **single composition root** per app (`LifecycleManager`) wires those dependencies together. That is what makes the code **testable without monkeypatching and without import-order surprises**.

## Architecture

Every app is a **one-directional tree** below its composition root. Imports point downward only. In Python, just as in Node.js, nothing at compile time rejects a cycle between modules, which opens the door to spaghetti code faster than ever, especially in the era of AI-assisted coding. That tree is the dependency graph of the modules. **Keeping it one-directional is what makes the app stable, predictable, and testable**, and it **reduces token consumption** because an AI agent can follow the imports instead of searching the whole repository.

The polyrepos kept `clients/`, `logger/`, `middlewares/`, `prometheus/`, and `distribution/` inside the app. Here those are shared packages. The app keeps its protocol surface, its state, and its services, and imports the rest, which honors DRY and keeps that infrastructure reusable across apps.

`lifecycle/` is the one package allowed to import every layer. `models/`, `config/`, and `metrics/` are cross-cutting: any layer may import them, and they import no layer. The shared packages sit below everything and import no app.

### FastAPI

```
                         main.py
                            |
                       lifecycle/          composition root: builds the graph
                            |
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   HTTP layer          routes/                 FastAPI routers
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
                       state/                  typed AppState + accessors
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Service layer       services/               business logic owned by this app
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Shared packages     shared_redis  shared_postgres  <key>_db
                       shared_middlewares  fastapi_middlewares  shared_prometheus
                       shared_log_manager  shared_config  shared_distribution

   Cross-cutting inside the app, importable from any layer, importing none:
       models/     config/     metrics/
```

A route calls a service; a service calls an injected client. The forbidden contract keeps `fastapi` and `starlette` out of `services`, `metrics`, and `config`.

### FastMCP

```
                         main.py
                            |
                       lifecycle/          composition root: builds the graph
                            |
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Protocol surface    http_routes/  mcp_primitives/
                                               custom HTTP routes, MCP tools, resources, prompts
                                               siblings: neither imports the other
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
                       state/                  typed AppState + accessors
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Service layer       services/               business logic owned by this app
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Shared packages     shared_redis  shared_middlewares  shared_prometheus
                       shared_log_manager  shared_config  shared_distribution

   Cross-cutting inside the app, importable from any layer, importing none:
       models/     config/     metrics/
```

A registrator calls a service; a service calls an injected client. Registration goes through `register_<feature>` functions only. The forbidden contract keeps `fastmcp`, `fastapi`, and `starlette` out of `services`, `metrics`, and `config`.

### Task runner

```
                         main.py               awaits TaskRunner.run() inside create_task_runner()
                            |
                       lifecycle/              composition root: builds, starts, tears down
                            |
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Orchestration       task_runner/            which services run, in which order
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
                       state/                  typed AppState; TaskRunner receives AppServices only
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Service layer       services/               business logic owned by this app
   . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . . . .
                            v
   Shared packages     github_client  shared_log_manager  shared_config  shared_distribution

   Cross-cutting inside the app, importable from any layer, importing none:
       config/
```

`TaskRunner` calls a service and receives `AppServices` only, so it cannot reach a client. The runner stays thin: data transformation, retries, or I/O there means a service is missing. The forbidden contract keeps every web framework out of `services` and `config`. A task runner has no server port.

### Benefits of a single composition root

Python will import `A` while `B` is still half-initialized, so construction order becomes whoever got imported first instead of a decision the composition root made. Tests then cannot build one dependency without dragging in the other, which is how suites slide into monkeypatching and process-wide setup. One `LifecycleManager` starts resources in topological order and tears them down in reverse.

### Avoiding hidden cyclic dependencies

A cycle is module `A` importing module `B` while `B` imports `A`. Neither module can be loaded on its own. That is not a style nit.

Import Linter only sees **directory-sized** layers. Two modules in the same package that import each other still compile, still pass, and are still a cycle. That is the developer's job. Everything at the directory level is enforced: `ci_scripts/lint_app_imports.py` runs `lint-imports` with each installed app's own contract, in the Lint workflow and in the pre-commit hook. A new top-level package under an app fails the exhaustive contract until it is placed in the hierarchy.

## Shared packages

| Directory | Import | Owns |
| --- | --- | --- |
| `packages/config` | `shared_config` | Resource config models and loaders, plus the `/livez`, `/readyz`, and `/metrics` path constants. Each app composes its own `AppConfig` from the models. |
| `packages/log_manager` | `shared_log_manager` | `LogManager`, structured JSON logging, uvicorn and stdlib bridges, the shared pytest logger fixture. |
| `packages/middlewares` | `shared_middlewares` | Correlation id middleware, the unhandled-exception handler, request-id header constants. |
| `packages/fastapi_middlewares` | `fastapi_middlewares` | FastAPI-only middleware such as secure headers. |
| `packages/redis` | `shared_redis` | `RedisClient`. Key helpers prefix every key with the app name. |
| `packages/postgres` | `shared_postgres` | `PostgresClient`. The connection only; no ORM models. |
| `packages/prometheus` | `shared_prometheus` | `PrometheusManager`. It mounts `/metrics` and excludes the probe and scrape paths from default HTTP series. |
| `packages/distribution` | `shared_distribution` | `installed_app_version` for the `app.version` log field. |
| `packages/feature_flags_db` | `feature_flags_db` | The `feature_flags` table and its Alembic history. |
| `packages/github_client` | `github_client` | `GithubClient` and `GithubAdapter` for the task-runner blueprint. Settings are `GithubClientConfig` in `shared_config`. |

The names follow three rules. `shared_*` is a library any app category can use. A package that imports one framework uses that framework's name (`fastapi_middlewares`). A logical database uses its key (`feature_flags_db`), and a client for one kind of app uses the client's name (`github_client`). Every package has its own README describing what belongs in it and what does not.

A client for an external resource lives in `python/packages/`, even when only one app uses it. Postgres, Redis, and GitHub are the examples. Its settings model lives in `shared_config`. A service owned by one app, such as `FeatureFlagService` or `CsvReportWriter`, stays in that app. [`.cursor/skills/client-packages/SKILL.md`](.cursor/skills/client-packages/SKILL.md) is the rule and its examples.

## Layout

```text
.
├── README.md
├── LICENSE
├── compose.yaml                      Redis and Postgres; HTTP and migrate services follow add_app.py
├── .env.example                      one env file for every process; copy to .env
├── .pre-commit-config.yaml           ruff, pyright, lint-imports, uv audit
├── .cursor/
│   ├── rules/                        every Python file: invariants, logging, config, tests, naming
│   └── skills/                       scaffold-scripts, alembic, client-packages, add-app-category
├── scaffold_scripts/                 add, rename, delete apps and packages
├── ci_scripts/                       affected-test selection, lint-imports, workflow matrices
├── .github/
│   ├── workflows/                    tests, lint, blueprints, image, audit
│   └── dependabot.yml
└── python/
    ├── pyproject.toml                uv workspace, ruff, pyright, pytest
    ├── uv.lock
    ├── .python-version               3.14
    ├── .dockerignore                 the image build context is this directory
    ├── packages/                     shared packages, one directory each
    ├── apps/                         your apps; empty until you add one
    └── _templates/
        ├── fastapi/                  blueprint; import package app; not a workspace member
        ├── fastmcp/
        └── task_runner/
```

Each blueprint keeps the import package `app`. The scaffold script renames it to the app name on install. A template change is applied by editing the blueprint, not the installed copy.

## Working with the monorepo

### Requirements

- Python 3.14 (pinned in `python/.python-version`; `uv` installs it)
- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://docs.docker.com/desktop/) (Compose v2) for the local stack and for HTTP app integration and e2e tests

### Setup

From the repository root:

```bash
uv sync --directory python --all-packages --all-groups
uv run --directory python pre-commit install
cp .env.example .env
```

One `uv sync` installs every package and app into `python/.venv`. `pre-commit install` registers the Git hook once per clone. `.env.example` is a working local configuration for the Compose stack, not a list of placeholders; `.env` is git-ignored.

### Add an app

The argument order is the category, then the app name. The name matches `^[a-z][a-z0-9_]*$`.

```text
uv run --directory python python ../scaffold_scripts/add_app.py fastapi orders_api
Added fastapi app 'orders_api' on port 8081.

uv run --directory python python ../scaffold_scripts/add_app.py fastmcp shop_mcp
Added fastmcp app 'shop_mcp' on port 8082.

uv run --directory python python ../scaffold_scripts/add_app.py task_runner nightly_export
Added task_runner app 'nightly_export'.
```

`orders_api` becomes distribution `orders-api`, import package `orders_api`, and env prefix `ORDERS_API`. The command copies the blueprint into `python/apps/orders_api`, rewrites the import package and the import-linter contract, registers the app in `python/pyproject.toml` (workspace member, root dependency, ruff, pyright), appends `ORDERS_API__SERVER__PORT` to `.env.example`, and runs `uv lock` and `uv sync`. After lock and sync, add and rename re-sort the installed app's imports with `ruff check --fix --select I`. An HTTP app gets the next free port above `8080`, read from `.env.example` and `compose.yaml`. A task runner gets none.

The command does not write `compose.yaml`. After it succeeds, add the app's service as [`.cursor/skills/scaffold-scripts/SKILL.md`](.cursor/skills/scaffold-scripts/SKILL.md) describes. That skill is what an AI agent follows when asked to add an app.

### Rename and delete an app

```text
uv run --directory python python ../scaffold_scripts/rename_app.py orders_api billing_portal
Renamed 'orders_api' to 'billing_portal'.

uv run --directory python python ../scaffold_scripts/delete_app.py shop_mcp
Deleted app 'shop_mcp'.
```

Rename keeps the category and the port. Delete removes the directory, the workspace registration, and the env lines immediately; there is no confirmation flag. When Compose still names the deleted app, delete prints a second line, `compose.yaml still references '<name>' on lines …`, and leaves `compose.yaml` unchanged. Both stop before writing when the source is missing or the target exists.

### Add, rename, and delete a package

```text
uv run --directory python python ../scaffold_scripts/add_package.py shared_widget
Added package 'shared_widget' at python/packages/widget.

uv run --directory python python ../scaffold_scripts/rename_package.py shared_widget shared_gadget
Renamed 'shared_widget' to 'shared_gadget'.

uv run --directory python python ../scaffold_scripts/delete_package.py shared_gadget
Deleted package 'shared_gadget'.
```

The argument is the import name. A leading `shared_` is not part of the directory, so `shared_widget` lives in `packages/widget` with distribution `shared-widget`; `github_client` keeps its name as the directory. Add writes an empty src-layout package and registers it, including pytest `testpaths`. Rename rewrites every import and `pyproject.toml` under `python/`, templates included. Delete refuses while any app, package, or template still requires the package:

```text
Package 'shared_gadget' is still required by orders_api, template fastapi.
```

A database package also needs an Alembic tree, an inventory line in `.env.example`, and a migrate service. Those are [`.cursor/skills/alembic/SKILL.md`](.cursor/skills/alembic/SKILL.md), not the script.

## Running

### One app

From the repository root, with Redis and Postgres up:

```bash
docker compose up -d --wait redis postgres
uv run --directory python/apps/orders_api orders-api
```

The console script is the distribution name. HTTP apps publish Kubernetes probes at `GET /livez` and `GET /readyz` and a Prometheus scrape at `GET /metrics`. A FastAPI app serves its docs at `/docs`; a FastMCP app serves MCP at `/mcp`. A task runner runs once and exits.

### Everything

```bash
docker compose up --build
```

Compose starts Redis, Postgres, one migrate service per logical database, and every HTTP app you have added. Containers get `REDIS__HOST=redis` and `POSTGRES__HOST=postgres`; host processes keep `127.0.0.1` from `.env`. Hosts are `127.0.0.1`, not `localhost`, so Windows does not stall on IPv6 while Docker Desktop publishes IPv4 only.

A task runner is not part of `docker compose up`. Its service carries a Compose profile, and you run it on its own:

```bash
docker compose --profile nightly-export run --build --rm nightly-export
```

Stop the stack with `docker compose down`. Add `-v` to wipe the Postgres volume.

## Configuration

One `.env` at the repository root. Every process reads it by absolute path, so the working directory does not matter, and the process environment wins over the file. `MONOREPO_ROOT` overrides the root discovery, which is how a container with no `.env` finds its settings.

Shared resources are `RESOURCE__FIELD`: `REDIS__HOST`, `POSTGRES__USER`, `PROMETHEUS__SHOULD_GZIP`. Per-app process settings are `APP__RESOURCE__FIELD` with the app directory name uppercased: `ORDERS_API__SERVER__PORT`, `ORDERS_API__LOGGER__MIN_LOG_LEVEL`. `PORT` has no default, so two apps cannot both bind `8080` by accident.

Postgres database names are an inventory, keyed by logical database rather than by app: `POSTGRES__FEATURE_FLAGS__DATABASE=feature_flags`. `create_postgres_config("feature_flags")` reads that line. Two apps that pass the same key share the database. A bare `POSTGRES__DATABASE` is rejected.

Each app composes a plain `AppConfig` from the `shared_config` loaders and calls the production validators it needs. Validation is strict and fails at startup: `debug` logging and `POSTGRES__SSL_MODE=disable` are rejected when `ENV=prod`. [`python/packages/config/README.md`](python/packages/config/README.md) lists every loader.

## Logging

Every record is one JSON object, including uvicorn lines, so the same keys can be filtered in grep or in Grafana, Datadog, or Groundcover. `shared_log_manager` provides `LogManager`; each app's composition root builds one and hands out named children through `get_child_logger(name)`. There is no process-wide `structlog.configure()` and no module-level logger.

```json
{"context": "OrdersService", "env": "local", "app": "orders-api", "instance": "api-1", "app.version": "0.1.0", "level": "info", "ts": "2026-11-07T00:00:00.000000Z", "msg": "order.created", "order_id": "o-42", "correlation_id": "6f1d3c2a-9b4e-4c11-8a2f-0e7b1d4a9c33"}
```

- `context` is the component: the `get_child_logger` name, a route name, or a bridge such as `uvicorn`.
- `env`, `app`, `instance`, and `app.version` are stamped by the manager. Call sites never pass them.
- `correlation_id` is bound by the shared middleware on HTTP apps, so the route, the service, and the client share it.
- `msg` is a short lowercase dotted event. Variable data goes in keyword fields.

Uncaught `asyncio` and `sys.excepthook` paths, and uvicorn's loggers, are rewritten onto those children. A task runner also bridges the root stdlib logger so third-party SDK warnings land in the same stream.

## Schema migrations

Models and migrations for one logical database live in `python/packages/<key>_db`. Alembic is a separate entry point from any app; it builds its own synchronous engine from `POSTGRES__*` and never constructs a client or a `LifecycleManager`.

```bash
uv run --directory python alembic -c packages/feature_flags_db/alembic.ini upgrade head
```

Compose runs that command in a one-shot migrate service before the apps that use the database start. Replicas never migrate. Create a revision with `alembic -c <that ini> revision --autogenerate -m "..."` and review it before committing. The procedure, including a new database, is [`.cursor/skills/alembic/SKILL.md`](.cursor/skills/alembic/SKILL.md).

## Container images

Each app has a Dockerfile, built from the `python/` directory so one context holds the lockfile, every package, and every app:

```bash
cd python
docker build -f apps/orders_api/Dockerfile .
```

The image is multi-stage and non-root, installs the one app with `uv sync --frozen --package <distribution> --no-dev --no-editable`, and sets `MONOREPO_ROOT=/app`. `python/.dockerignore` keeps the virtualenv, caches, tests, and blueprints out of the context. The default command starts the app; a migrate service overrides it with the Alembic command. There is no deploy workflow: where an image goes is a product decision.

## Testing

Shared packages run as one suite from `python/`:

```bash
uv run --directory python pytest
```

Each app runs on its own, per directory:

```bash
uv run --directory python/apps/orders_api pytest
uv run --directory python/apps/orders_api pytest tests/unit
```

An app has `tests/unit`, and `tests/integration` and `tests/e2e` when the blueprint ships them. Unit tests are in-process with injected doubles. HTTP app integration and e2e tests start Redis and Postgres through Testcontainers, so Docker must be running. The task-runner blueprint's end-to-end test calls the real GitHub API and needs a network, not Docker. A skipped suite is not a pass. `monkeypatch` and `unittest.mock.patch` are forbidden; inject the dependency.

## Linting and type checking

From `python/`:

```bash
uv run ruff format .
uv run ruff check .
uv run pyright
uv run python ../ci_scripts/lint_app_imports.py
```

[Ruff](https://docs.astral.sh/ruff/) formats and lints: 100-column lines, double quotes, Google-style docstrings, import sorting, no `print`. [Pyright](https://microsoft.github.io/pyright/) runs in strict mode over every package and app. Import Linter runs with each installed app's own contract. `ci_scripts/` and `scaffold_scripts/` have the same checks, run with `uv run --directory <dir> --project ../python`.

## Pre-commit hooks

The root [`.pre-commit-config.yaml`](.pre-commit-config.yaml) runs ruff format (as a check), ruff check, and pyright for `python/`, `ci_scripts/`, and `scaffold_scripts/`, then `lint-imports` for every installed app, then `uv audit --locked`. No pytest and no Docker in the hook. Install it once per clone:

```bash
uv run --directory python pre-commit install
```

## CI

[`tests.yml`](.github/workflows/tests.yml) is the smart one. A `select` job runs [`ci_scripts/select_affected.py`](ci_scripts/README.md), which reads the workspace dependency graph and diffs the change: a pull request against its base, a push to `main` against the previous commit. A file under a package selects that package and every package or app that depends on it. A file under an app selects that app only. The workspace `pyproject.toml`, the lockfile, the Python version, the workflows, the selector itself, and a dependency-spec change in any member select everyone. Then one job runs per selected package and one per existing suite of each selected app, named `App orders_api (unit)` and so on, each with `pytest -v`.

[`lint.yml`](.github/workflows/lint.yml) runs ruff, pyright, and `lint-imports` for every installed app, plus the script trees.

[`blueprints.yml`](.github/workflows/blueprints.yml) discovers the categories under `python/_templates/`, scaffolds a fresh app from each with `add_app.py`, and runs ruff check, ruff format, pyright, `lint-imports`, and the app's full test suite on it, Docker included. It triggers on changes to the blueprints, the shared packages, the scaffold scripts, or the workspace files, so a template regression is caught before anyone stamps it out.

[`image.yml`](.github/workflows/image.yml) discovers the apps that have a Dockerfile and builds each image with no push. [`audit.yml`](.github/workflows/audit.yml) runs `uv audit --locked` on push, pull request, and every Monday, so a CVE published while `main` is idle still fails the badge. [`dependabot.yml`](.github/dependabot.yml) opens weekly PRs for the `uv` lockfile and for GitHub Actions.

Every workflow discovers apps by directory. Adding or deleting an app needs no CI edit.

## AI rules and skills

Rules are split so each is written once. [`.cursor/rules/`](.cursor/rules) applies to every Python file:

- `invariants` zero global state; only `lifecycle` and `main` construct the graph
- `logging` loggers are injected; the composition root is the only place that builds them
- `config` config fields match env names; durations are ints with a unit suffix
- `tests` test layout, nearest fixtures, and the ban on monkeypatching
- `docstrings` Google-style docstrings on every module, class, and function
- `file-naming` module filenames name the concept, readable without their directory
- `variable-naming` dicts are `<value>_by_<key>`; sorted lists use `asc_by_` / `desc_by_`; for-loop headers stay a short name
- `final` never-reassigned constants and attributes are `Final`

Each blueprint's `.cursor/rules/` holds only what that category does differently: its architecture layers, where a route or a primitive gets its logger, how its tests reach a real store. `add_app.py` copies that directory into the new app.

Skills are the procedures an agent follows:

- [`scaffold-scripts`](.cursor/skills/scaffold-scripts/SKILL.md) add, rename, delete apps and packages, and the Compose edits that follow
- [`alembic`](.cursor/skills/alembic/SKILL.md) a logical database, its Alembic history, and its migrate service
- [`client-packages`](.cursor/skills/client-packages/SKILL.md) whether a client or service belongs in `python/packages/` or stays in one app
- [`add-app-category`](.cursor/skills/add-app-category/SKILL.md) a fourth blueprint and the script edits that teach `add_app.py` about it

## Adding an app category

The three blueprints are a starting set, not a boundary. A worker that drains a queue, a gRPC server, or a CLI is a new directory under `python/_templates/` plus a handful of named edits in `scaffold_scripts/`. CI discovers blueprints and apps by directory, so no workflow changes. [`.cursor/skills/add-app-category/SKILL.md`](.cursor/skills/add-app-category/SKILL.md) is the procedure.

## Not shipped

Authentication is a product choice (JWT, sessions, mTLS, or a gateway that already did it), so no scheme ships. When you add one, identity is request-scoped: a route or primitive `Depends` on claims and passes `user_id` into the service method, and the verifier is constructed in `lifecycle/` like every other dependency. Each HTTP blueprint carries an `auth` rule and a `state/README.md` section with that shape, so an AI-assisted edit follows it. The [FastAPI polyrepo README](https://github.com/ori88c-python-templates/fastapi-polyrepo-template#authentication) has worked JWT and session examples.

Kubernetes manifests and Helm charts are not included: the images, probes, and migrate-then-start contract are what a later chart should implement.

## License

[MIT](LICENSE).
