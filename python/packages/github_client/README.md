# github-client

GitHub client and the adapter that turns a search page into records. Distribution `github-client`, import `github_client`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Env names](#env-names)
- [Exports](#exports)
- [Testing](#testing)

## Belongs here

- `GithubClient`: `start`, `stop`, and `search_repositories_by_stars`. Construct it with `app_name` (`validate_app_name`). That value is the GitHub user agent.
- `GithubAdapter`: one organization's most-starred repositories, as `GithubRepoInfo`. An unknown organization (HTTP 422) becomes `GithubOrganizationNotFoundError`.

`githubkit` is a dependency of this package. Apps that do not talk to GitHub do not depend on it. It is not `shared_*`.

## Does not belong here

- `GithubClientConfig` and `load_github_client_config`. Those are `shared_config`.
- A CSV writer, a report path, or any other service owned by one app.
- A test double. There is no `github_client.testing`.

## Env names

`load_github_client_config("github_report")` in `shared_config` reads `GITHUB_REPORT__GITHUB__*`:

- `ORG_URL` (default `https://github.com/microsoft`)
- `REPOS_LIMIT` (default `4`, from 1 to 100)
- `TOKEN` (optional, never logged)
- `REQUEST_TIMEOUT_SECONDS` (default `10`)

## Exports

Import from `github_client`:

- `GithubClient`, `GithubAdapter`, `GithubOrganizationNotFoundError`, `GithubRepoInfo`

## Testing

Tests live in this package. One directory per module, then one file per behaviour. There is no `tests/unit/` or `tests/integration/` segment.

- `tests/github_client/` covers authorization, the search request, `start`, `stop`, and `test_live_search.py`. That directory has no `__init__.py`. Pytest's import mode would otherwise put `tests/` on the path and load this folder as the `github_client` package. `tests/` itself also has no `__init__.py`: `shared_log_manager` already has one, and a second top-level `tests` package collides with it.
- `tests/github_adapter/test_get_popular_repos.py`
- `test_live_search.py` is marked `integration` and calls `api.github.com`. The default `uv run pytest` from `python/` runs it. A skip is not a pass.
- Request the `log_manager` fixture. Do not construct a `LogManager`. Read lines with `read_records` from `shared_log_manager.testing`.
- `tests/fakes/fake_github_search.py` is a helper for this suite. Pytest adds that directory to `pythonpath`. It is not the `tests/` directory, so it does not shadow the `github_client` import. Do not import it from an app.
