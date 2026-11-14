"""Per-app bind address. PORT is required so two apps cannot share 8080."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared_config import ServerConfig, create_server_config


def test_port_is_required_and_host_defaults(tmp_path: Path) -> None:
    """A missing port fails. An omitted host still binds all interfaces."""
    env_file = tmp_path / ".env"
    env_file.write_text("BILLING_API__SERVER__PORT=8081\n", encoding="utf-8")
    config = create_server_config("billing_api", env_file=env_file)
    assert config.PORT == 8081
    assert config.HOST == "0.0.0.0"  # noqa: S104


def test_two_apps_take_different_ports_from_one_file(tmp_path: Path) -> None:
    """One env file can launch both processes without a port collision."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BILLING_API__SERVER__PORT=8081\nPEOPLE_API__SERVER__PORT=8082\n",
        encoding="utf-8",
    )
    assert create_server_config("billing_api", env_file=env_file).PORT == 8081
    assert create_server_config("people_api", env_file=env_file).PORT == 8082


def test_lowercase_prefix_matches(tmp_path: Path) -> None:
    """Env names are case-insensitive. The app name itself stays lowercase."""
    env_file = tmp_path / ".env"
    env_file.write_text("billing_api__server__port=9090\n", encoding="utf-8")
    assert create_server_config("billing_api", env_file=env_file).PORT == 9090


def test_missing_port_is_rejected(tmp_path: Path) -> None:
    """The polyrepo default of 8080 would hide a second app on the same port."""
    env_file = tmp_path / ".env"
    env_file.write_text("BILLING_API__SERVER__HOST=127.0.0.1\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        create_server_config("billing_api", env_file=env_file)


def test_port_outside_the_tcp_range_is_rejected(tmp_path: Path) -> None:
    """Zero and values above 65535 are not ports."""
    env_file = tmp_path / ".env"
    env_file.write_text("BILLING_API__SERVER__PORT=0\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        create_server_config("billing_api", env_file=env_file)


def test_hyphenated_app_name_is_rejected(tmp_path: Path) -> None:
    """billing-api and billing_api would otherwise share one env prefix."""
    env_file = tmp_path / ".env"
    env_file.write_text("BILLING_API__SERVER__PORT=8081\n", encoding="utf-8")
    with pytest.raises(ValueError, match="app name"):
        create_server_config("billing-api", env_file=env_file)


def test_direct_construction_still_requires_a_port() -> None:
    """Tests and apps can build the model without the environment, but not without a port."""
    with pytest.raises(ValidationError):
        ServerConfig.model_validate({})
