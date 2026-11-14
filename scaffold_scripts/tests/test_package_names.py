"""Package import names and the shared_ directory rule."""

import pytest

from helpers.errors import ScaffoldError
from helpers.package_names import identity_for_new_package


def test_shared_prefix_is_not_part_of_the_directory() -> None:
    """shared_redis lives in packages/redis and is distributed as shared-redis."""
    identity = identity_for_new_package("shared_redis")

    assert identity.import_name == "shared_redis"
    assert identity.directory == "redis"
    assert identity.distribution_name == "shared-redis"


def test_a_name_without_the_prefix_uses_the_import_as_the_directory() -> None:
    """github_client and feature_flags_db keep the import name as the directory."""
    client = identity_for_new_package("github_client")
    database = identity_for_new_package("feature_flags_db")

    assert client.directory == "github_client"
    assert client.distribution_name == "github-client"
    assert database.directory == "feature_flags_db"
    assert database.distribution_name == "feature-flags-db"


def test_shared_prefix_alone_is_rejected() -> None:
    """Stripping shared_ must still leave a directory name."""
    with pytest.raises(ScaffoldError, match=r"Package import name 'shared_' must match"):
        identity_for_new_package("shared_")


def test_hyphenated_import_names_are_rejected() -> None:
    """Distribution hyphens are derived, not accepted as the import name."""
    with pytest.raises(ScaffoldError, match="shared-widget"):
        identity_for_new_package("shared-widget")
