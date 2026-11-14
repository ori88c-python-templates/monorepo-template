# tests

The test suite, split by how much of the real world a test is allowed to touch.

## Table of Contents

- [Layout](#layout)
- [Running](#running)

## Layout

| Path | What belongs there |
| --- | --- |
| [`unit/`](unit/README.md) | In-process tests. Dependencies are injected. |
| [`e2e/`](e2e/README.md) | The whole process, from `main` to its exit code. Needs a network. |

Within each tree, layout mirrors `src/app/`: one directory per package, then one
directory per component under test, then one file per feature.

The live GitHub search is `github_client`'s `test_live_search.py`, not a tree here.

## Running

```bash
uv run pytest
uv run pytest tests/unit
uv run pytest tests/e2e
```

`testpaths` lists `tests/unit`, then `tests/e2e`. Unit tests are offline.
End-to-end calls GitHub.
