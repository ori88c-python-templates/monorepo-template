"""The editable install of this app reports a version string."""

from app.config import APP_NAME
from shared_distribution import installed_app_version


def test_this_checkout_reports_a_non_empty_version() -> None:
    """The editable ``.pth`` install in this environment yields a version string."""
    result = installed_app_version(APP_NAME)

    assert isinstance(result, str)
    assert result
