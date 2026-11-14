"""Process identity fields stamped on every LogManager record."""

import socket
from io import BytesIO

import pytest

from shared_config import Environment, LoggerConfig
from shared_log_manager import LogManager
from shared_log_manager.testing import ManagerFactory, read_records


def test_every_record_carries_resource_fields(
    make_manager: ManagerFactory,
    sink: BytesIO,
) -> None:
    """env, app, instance, and app.version are present with their gold-standard values."""
    log = make_manager(
        env=Environment.STAGING,
        app_version="9.9.9",
    ).get_child_logger("UsersService")

    log.info("user.created")

    (record,) = read_records(sink)
    assert record["env"] == Environment.STAGING.value
    assert record["app"] == "billing-api"
    assert record["instance"] == socket.gethostname()
    assert record["app.version"] == "9.9.9"


def test_two_managers_do_not_share_env(make_manager: ManagerFactory, sink: BytesIO) -> None:
    """A second manager's env does not leak into the first manager's records."""
    other_sink = BytesIO()
    first = make_manager(stream=sink)
    second = make_manager(env=Environment.PROD, stream=other_sink)

    first.get_child_logger("First").info("first.event")
    second.get_child_logger("Second").info("second.event")

    (first_record,) = read_records(sink)
    (second_record,) = read_records(other_sink)
    assert first_record["env"] == Environment.DEV.value
    assert second_record["env"] == Environment.PROD.value


def test_empty_app_name_is_rejected() -> None:
    """A blank app field would make every record untraceable."""
    with pytest.raises(ValueError, match="app_name"):
        LogManager(
            LoggerConfig(),
            env=Environment.DEV,
            app_version="0.1.0",
            app_name="",
        )
