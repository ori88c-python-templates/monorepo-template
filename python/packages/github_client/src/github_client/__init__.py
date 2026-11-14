"""GitHub client and the adapter that turns search items into records.

Apps that do not talk to GitHub do not depend on this package. ``githubkit``
stays here so it is not pulled into every app.
"""

from github_client.github_adapter import GithubAdapter
from github_client.github_adapter_errors import GithubOrganizationNotFoundError
from github_client.github_client import GithubClient
from github_client.github_repo_info import GithubRepoInfo

__all__ = [
    "GithubAdapter",
    "GithubClient",
    "GithubOrganizationNotFoundError",
    "GithubRepoInfo",
]
