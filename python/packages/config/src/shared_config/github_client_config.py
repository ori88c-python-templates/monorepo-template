"""Settings for talking to GitHub. The CSV path stays in the app."""

from pathlib import Path
from typing import Final, Self

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator

from shared_config.loading import USE_ROOT_ENV, UseRootEnv, load_app_resource

_GITHUB_HOST: Final = "github.com"
_RESOURCE: Final = "GITHUB"


class GithubClientConfig(BaseModel):
    """Which organization to query, and how to authenticate to GitHub.

    The output directory of a report is not here. That setting belongs to the
    app that writes the file.

    Attributes:
        ORG_URL: Browser URL of the organization, e.g. ``https://github.com/microsoft``.
            A URL rather than a bare login because that is what a human copies from the
            address bar; the login is derived by ``ORG_NAME``.
        REPOS_LIMIT: How many of the most-starred repositories to present. Capped at
            100, the Search API's page size, so the report is exactly one request.
        TOKEN: Optional personal access token. Unauthenticated search allows 10
            requests a minute, authenticated 30. Never logged.
        REQUEST_TIMEOUT_SECONDS: httpx timeout for every GitHub request. ``githubkit``
            defaults to no timeout at all, which would let a stalled connection hang the
            run forever.
    """

    ORG_URL: HttpUrl = HttpUrl("https://github.com/microsoft")
    REPOS_LIMIT: int = Field(default=4, ge=1, le=100)
    TOKEN: SecretStr | None = None
    REQUEST_TIMEOUT_SECONDS: int = Field(default=10, ge=1)

    @model_validator(mode="after")
    def _require_organization_url(self) -> Self:
        """Reject URLs that do not point at exactly one GitHub organization.

        Returns:
            The validated model.

        Raises:
            ValueError: If the host is not ``github.com``, or the path is not a single
                segment (``/microsoft``), such as a repository URL or the bare site root.
        """
        if self.ORG_URL.host != _GITHUB_HOST:
            message = f"GITHUB__ORG_URL must point at {_GITHUB_HOST}."
            raise ValueError(message)
        if not self._path_segments():
            message = (
                f"GITHUB__ORG_URL must name an organization, e.g. https://{_GITHUB_HOST}/microsoft."
            )
            raise ValueError(message)
        if len(self._path_segments()) > 1:
            message = "GITHUB__ORG_URL must be an organization URL, not a repository URL."
            raise ValueError(message)
        return self

    @property
    def ORG_NAME(self) -> str:
        """The organization's login, as the GitHub API expects it.

        Returns:
            The single path segment of ``ORG_URL``, without slashes.
        """
        return self._path_segments()[0]

    def _path_segments(self) -> list[str]:
        """Split the URL path into its non-empty segments.

        A trailing slash (``https://github.com/microsoft/``) is a common copy-paste
        artefact and yields the same single segment.

        Returns:
            The path segments, in order.
        """
        path = self.ORG_URL.path or ""
        return [segment for segment in path.split("/") if segment]


def load_github_client_config(
    app_name: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> GithubClientConfig:
    """Load ``<APP>__GITHUB__*`` for ``app_name``.

    Args:
        app_name: App directory name, such as ``github_report``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        Validated GitHub settings. Unset fields keep the demo defaults.

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier.
        ValidationError: If a value is invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_app_resource(GithubClientConfig, app_name, _RESOURCE, env_file=env_file)
