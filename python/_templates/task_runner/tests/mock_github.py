"""Mock GitHub SDK for lifecycle tests. Not the package's test helper.

The JSON is the same two-item payload the client package uses. This file does
not import ``github_client``'s tests.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import httpx2 as httpx
from githubkit import GitHub
from githubkit.auth import UnauthAuthStrategy

_FAKE_PATH: Final = Path(__file__).with_name("fake_github_search.json")
FAKE_GITHUB_SEARCH: Final[dict[str, Any]] = json.loads(_FAKE_PATH.read_text(encoding="utf-8"))
FAKE_RATE_LIMIT: Final[dict[str, Any]] = {
    "resources": {
        "core": {"limit": 60, "remaining": 59, "reset": 1700000000, "used": 1},
        "search": {"limit": 10, "remaining": 9, "reset": 1700000000, "used": 1},
    }
}
_RATE_LIMIT_PATH: Final = "/rate_limit"
_SEARCH_PATH: Final = "/search/repositories"


@dataclass
class MockGithub:
    """A githubkit client on ``MockTransport``, plus the requests it received.

    Attributes:
        github: Pass this to ``LifecycleManager(..., github=...)``.
        requests: Every HTTP request the transport handled, in order.
    """

    github: GitHub[Any]
    requests: list[httpx.Request] = field(default_factory=lambda: [])


def mock_github() -> MockGithub:
    """Build an SDK instance that answers ``/rate_limit`` and ``/search/repositories``.

    Returns:
        The SDK instance and the list that will collect every request it makes.
    """
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Route the two endpoints the client uses and record the request.

        Args:
            request: The outgoing call githubkit built.

        Returns:
            A canned response, or 404 for any other path.
        """
        requests.append(request)
        path = request.url.path
        if path.endswith(_RATE_LIMIT_PATH):
            return httpx.Response(200, json=FAKE_RATE_LIMIT)
        if path.endswith(_SEARCH_PATH):
            return httpx.Response(200, json=FAKE_GITHUB_SEARCH)
        return httpx.Response(404, json={"message": "Not Found"})

    github = GitHub(
        UnauthAuthStrategy(),
        async_transport=httpx.MockTransport(handler),
        http_cache=False,
        auto_retry=False,
    )
    return MockGithub(github=github, requests=requests)
