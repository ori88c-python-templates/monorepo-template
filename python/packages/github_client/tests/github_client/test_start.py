"""``start`` probes ``/rate_limit`` and logs the remaining quota."""

from io import BytesIO

import pytest
from fake_github_search import MakeClient

from github_client import GithubClient
from shared_config import GithubClientConfig
from shared_log_manager import LogManager
from shared_log_manager.testing import read_records


async def test_start_probes_rate_limit_and_logs_remaining(
    make_client: MakeClient,
    sink: BytesIO,
) -> None:
    """The probe is the first request, and the leftover search and core quota are logged."""
    client, mocked = make_client()

    await client.start()

    try:
        (request,) = mocked.requests
        assert request.url.path.endswith("/rate_limit")
        (record,) = [record for record in read_records(sink) if record["msg"] == "github.started"]
        assert record["search_remaining"] == 9
        assert record["core_remaining"] == 59
        assert record["context"] == "GithubClient"
    finally:
        await client.stop()


def test_app_name_must_be_an_identifier(log_manager: LogManager) -> None:
    """The user agent is the app directory name, not a hyphenated distribution name."""
    with pytest.raises(ValueError, match="app name"):
        GithubClient(
            GithubClientConfig(),
            log_manager.get_child_logger("GithubClient"),
            "github-report",
        )
