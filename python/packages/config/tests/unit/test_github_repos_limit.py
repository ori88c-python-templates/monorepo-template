"""``REPOS_LIMIT`` is one Search API page: 1 to 100."""

import pytest
from pydantic import ValidationError

from shared_config import GithubClientConfig


def test_default_limit_is_four() -> None:
    """The demo reports four repositories unless the environment says otherwise."""
    assert GithubClientConfig().REPOS_LIMIT == 4


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_outside_one_search_page_is_rejected(limit: int) -> None:
    """Zero is empty and 101 would need a second page the client does not fetch."""
    with pytest.raises(ValidationError):
        GithubClientConfig(REPOS_LIMIT=limit)
