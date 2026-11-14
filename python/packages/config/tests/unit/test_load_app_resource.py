"""An app-owned model is loaded from ``<APP>__<RESOURCE>__*``."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from shared_config import load_app_resource


class _Widget(BaseModel):
    """Stand-in for a model that does not belong in this package."""

    org_url: str = "https://example.test"
    limit: int = 1


def test_prefixed_fields_fill_the_model(tmp_path: Path) -> None:
    """The app name and the resource segment both sit in front of the leaf."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GITHUB_REPORT__GITHUB__ORG_URL=https://github.com/microsoft\n"
        "GITHUB_REPORT__GITHUB__LIMIT=4\n",
        encoding="utf-8",
    )
    loaded = load_app_resource(_Widget, "github_report", "GITHUB", env_file=env_file)
    assert loaded.org_url == "https://github.com/microsoft"
    assert loaded.limit == 4


def test_another_apps_prefix_is_ignored(tmp_path: Path) -> None:
    """Two apps can share one file without reading each other's resource."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BILLING_API__GITHUB__ORG_URL=https://github.com/acme\nGITHUB_REPORT__GITHUB__LIMIT=9\n",
        encoding="utf-8",
    )
    loaded = load_app_resource(_Widget, "github_report", "GITHUB", env_file=env_file)
    assert loaded.org_url == "https://example.test"
    assert loaded.limit == 9


def test_unset_fields_keep_defaults(tmp_path: Path) -> None:
    """A missing leaf is the model's default, not an error."""
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    loaded = load_app_resource(_Widget, "github_report", "GITHUB", env_file=env_file)
    assert loaded.org_url == "https://example.test"
    assert loaded.limit == 1


def test_invalid_value_is_rejected(tmp_path: Path) -> None:
    """The target model is what validates the raw string."""
    env_file = tmp_path / ".env"
    env_file.write_text("GITHUB_REPORT__GITHUB__LIMIT=none\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_app_resource(_Widget, "github_report", "GITHUB", env_file=env_file)


@pytest.mark.parametrize("resource", ["github", "GITHUB-API", "1GITHUB", ""])
def test_resource_must_be_an_uppercase_identifier(tmp_path: Path, resource: str) -> None:
    """A lowercase or hyphenated segment would not match the env prefix rule."""
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="resource"):
        load_app_resource(_Widget, "github_report", resource, env_file=env_file)


def test_app_name_must_be_an_identifier(tmp_path: Path) -> None:
    """The app segment is the directory name, not a hyphenated distribution name."""
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="app name"):
        load_app_resource(_Widget, "github-report", "GITHUB", env_file=env_file)
