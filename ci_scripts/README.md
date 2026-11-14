# CI scripts

Four commands feed the workflows. `select_affected.py` chooses the tests a change requires. `lint_app_imports.py` runs import-linter for every installed app. `list_app_images.py` and `list_blueprints.py` build the matrices for the Image and Blueprints workflows.

## Matrices

`list_app_images.py` prints the directories under `python/apps` that hold a `Dockerfile`, sorted. `list_blueprints.py` prints the directories under `python/_templates` that hold a `pyproject.toml`. Both take `--repo-root` and an optional `--github-output`, which appends `apps=` or `categories=` as one JSON line. An empty `python/apps` prints `[]`, and the Image build job is skipped. A new blueprint directory is a new Blueprints job with no workflow edit.

```text
uv run --no-project python ci_scripts/list_app_images.py --repo-root .
uv run --no-project python ci_scripts/list_blueprints.py --repo-root .
```

## Import-linter

`lint_app_imports.py` runs `lint-imports --config apps/<name>/pyproject.toml` for each installed app and stops at the first failure. With no installed app it prints `No installed apps under python/apps. Nothing to lint.` and exits 0, so the shipped repository passes lint.

## Affected tests

`select_affected.py` prints the packages and apps whose tests a change requires.

```json
{"packages": ["config", "github_client"], "apps": ["nightly_export"]}
```

`--github-output` appends two lines for GitHub Actions and diffs `DIFF_BASE`. A pull request sets that to the base SHA. A push sets it to the previous commit. An empty value or an all-zero SHA selects every member, except a pull request with no base, which fails. `packages` is the package list. `app_suites` is `{app, suite}` for each existing `tests/unit`, `tests/integration`, or `tests/e2e` directory. An app with no `tests/integration` directory has no integration job. Stdout stays the JSON above.

A file under `python/packages/<name>/` selects that package and every package or app that depends on it, directly or through other packages. A file under `python/apps/<name>/` selects that app only. The node id is the directory name.

These changes select every member: `python/pyproject.toml`, `python/uv.lock`, `python/.python-version`, anything under `.github/workflows/` or `ci_scripts/`, and a member `pyproject.toml` whose `requires-python`, dependencies, or `[tool.uv.sources]` differ. A description-only edit of that file stays on the normal rule.

A blueprint path or a `scaffold_scripts/` path selects nothing. If the workspace cannot be read, the command exits non-zero and prints no JSON.

## Checks

Run this suite on its own. It imports `helpers`, and so does `scaffold_scripts`.

From the repository root:

```text
uv run --directory python python ../ci_scripts/select_affected.py --repo-root . --all
uv run --directory python python ../ci_scripts/select_affected.py --repo-root . --base origin/main
uv run --directory python python ../ci_scripts/select_affected.py --repo-root . --github-output "$GITHUB_OUTPUT"
uv run --directory python pytest ../ci_scripts/tests
uv run --directory ci_scripts --project ../python ruff check
uv run --directory ci_scripts --project ../python ruff format --check
uv run --directory ci_scripts --project ../python pyright
```
