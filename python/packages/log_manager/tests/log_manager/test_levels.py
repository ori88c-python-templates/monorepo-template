"""Minimum-level filtering, and the independence of separate managers."""

import io

import pytest

from shared_config import LogLevel
from shared_log_manager import LogManager
from shared_log_manager.testing import ManagerFactory, read_records

ALL_METHODS = ["debug", "info", "warning", "error", "critical"]


@pytest.mark.parametrize("method", ["debug", "info", "warning"])
def test_records_below_the_minimum_level_are_dropped(
    make_manager: ManagerFactory, sink: io.BytesIO, method: str
) -> None:
    """Filtering happens before any processor runs, so nothing reaches the stream."""
    log = make_manager(LogLevel.ERROR).get_child_logger("UsersService")

    getattr(log, method)("some.event")

    assert sink.getvalue() == b""


@pytest.mark.parametrize("method", ["error", "critical"])
def test_records_at_or_above_the_minimum_level_are_emitted(
    make_manager: ManagerFactory, sink: io.BytesIO, method: str
) -> None:
    """Everything from the configured level upwards still gets through."""
    log = make_manager(LogLevel.ERROR).get_child_logger("UsersService")

    getattr(log, method)("some.event")

    (record,) = read_records(sink)
    assert record["msg"] == "some.event"


def test_the_default_minimum_level_is_info(log_manager: LogManager, sink: io.BytesIO) -> None:
    """A LoggerConfig with nothing set drops debug but keeps info."""
    log = log_manager.get_child_logger("UsersService")

    log.debug("dropped")
    log.info("kept")

    (record,) = read_records(sink)
    assert record["msg"] == "kept"


def test_every_level_passes_when_the_minimum_is_debug(
    make_manager: ManagerFactory, sink: io.BytesIO
) -> None:
    """The most permissive setting filters nothing."""
    log = make_manager(LogLevel.DEBUG).get_child_logger("UsersService")

    for method in ALL_METHODS:
        getattr(log, method)("some.event")

    assert [record["level"] for record in read_records(sink)] == ALL_METHODS


def test_two_managers_with_different_levels_do_not_interfere(make_manager: ManagerFactory) -> None:
    """No shared configuration means no cross-talk between managers.

    This is the property a ``structlog.configure()``-based design cannot offer, and the
    reason logging here is testable at all.
    """
    verbose_sink, quiet_sink = io.BytesIO(), io.BytesIO()
    verbose = make_manager(LogLevel.DEBUG, stream=verbose_sink)
    quiet = make_manager(LogLevel.ERROR, stream=quiet_sink)

    verbose.get_child_logger("Verbose").debug("noisy")
    quiet.get_child_logger("Quiet").debug("noisy")

    (record,) = read_records(verbose_sink)
    assert record["context"] == "Verbose"
    assert quiet_sink.getvalue() == b""


def test_managers_write_only_to_their_own_stream(make_manager: ManagerFactory) -> None:
    """Each manager owns its stream; records never leak into another's."""
    first_sink, second_sink = io.BytesIO(), io.BytesIO()
    first = make_manager(stream=first_sink)
    second = make_manager(stream=second_sink)

    first.get_child_logger("First").info("first.event")
    second.get_child_logger("Second").info("second.event")

    assert [record["msg"] for record in read_records(first_sink)] == ["first.event"]
    assert [record["msg"] for record in read_records(second_sink)] == ["second.event"]
