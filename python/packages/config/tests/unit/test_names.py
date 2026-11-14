"""App directory names that can become env prefixes."""

import pytest

from shared_config import validate_app_name


def test_snake_case_name_is_returned_unchanged() -> None:
    """The directory name is the argument. The prefix is derived later."""
    assert validate_app_name("billing_api") == "billing_api"


@pytest.mark.parametrize("name", ["Billing", "billing-api", "1billing", "_billing", ""])
def test_names_that_would_collapse_prefixes_are_rejected(name: str) -> None:
    """Hyphens, capitals, and a leading digit are not identifiers."""
    with pytest.raises(ValueError, match="app name"):
        validate_app_name(name)
