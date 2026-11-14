"""The organization login is taken from a github.com URL of exactly one segment."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared_config import GithubClientConfig, load_github_client_config


def test_org_name_is_the_single_path_segment() -> None:
    """The default Microsoft URL yields the login the Search API expects."""
    assert GithubClientConfig().ORG_NAME == "microsoft"


def test_trailing_slash_is_ignored() -> None:
    """A copy-pasted URL with a trailing slash still names the organization."""
    config = GithubClientConfig.model_validate({"ORG_URL": "https://github.com/microsoft/"})

    assert config.ORG_NAME == "microsoft"


def test_non_github_host_is_rejected() -> None:
    """A GitLab or other host is not a GitHub organization URL."""
    with pytest.raises(ValidationError, match=r"must point at github\.com"):
        GithubClientConfig.model_validate({"ORG_URL": "https://gitlab.com/microsoft"})


def test_site_root_is_rejected() -> None:
    """``https://github.com/`` names no organization."""
    with pytest.raises(ValidationError, match="must name an organization"):
        GithubClientConfig.model_validate({"ORG_URL": "https://github.com/"})


def test_repository_url_is_rejected() -> None:
    """Two path segments is a repository, not an organization."""
    with pytest.raises(ValidationError, match="not a repository URL"):
        GithubClientConfig.model_validate({"ORG_URL": "https://github.com/microsoft/vscode"})


def test_loader_reads_the_github_segment(tmp_path: Path) -> None:
    """The env prefix is the app name plus ``GITHUB``, not a bare ``GITHUB_REPORT``."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GITHUB_REPORT__GITHUB__ORG_URL=https://github.com/python\n",
        encoding="utf-8",
    )
    loaded = load_github_client_config("github_report", env_file=env_file)
    assert loaded.ORG_NAME == "python"
