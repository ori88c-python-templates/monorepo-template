"""Search the real GitHub API for an organization's most-starred repositories."""

import os

import pytest
from pydantic import SecretStr

from github_client import GithubClient
from shared_config import load_github_client_config
from shared_log_manager import LogManager

pytestmark = pytest.mark.integration

_ORG: str = "microsoft"
_LIMIT: int = 3
_APP_NAME: str = "github_report"


async def test_search_returns_repos_in_non_increasing_star_order(
    log_manager: LogManager,
) -> None:
    """Three Microsoft repositories come back already ranked by stars.

    ``GITHUB_REPORT__GITHUB__TOKEN`` is read from the process environment. When that
    is unset and ``GITHUB_TOKEN`` is set, the test uses it. Otherwise the search is
    unauthenticated.
    """
    config = load_github_client_config(_APP_NAME, env_file=None)
    token = os.environ.get("GITHUB_TOKEN")
    if config.TOKEN is None and token:
        config = config.model_copy(update={"TOKEN": SecretStr(token)})
    config = config.model_copy(update={"REPOS_LIMIT": _LIMIT})
    client = GithubClient(
        config,
        log_manager.get_child_logger("GithubClient"),
        _APP_NAME,
    )
    await client.start()
    try:
        items = await client.search_repositories_by_stars(_ORG, _LIMIT)
    finally:
        await client.stop()

    assert len(items) == _LIMIT
    stars = [item.stargazers_count for item in items]
    assert stars == sorted(stars, reverse=True)
    assert all(item.name for item in items)
