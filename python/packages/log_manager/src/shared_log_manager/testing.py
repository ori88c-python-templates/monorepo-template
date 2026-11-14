"""Pytest fixtures for any package that logs through :class:`LogManager`.

Production code does not import this module. Pytest loads it through the
``pytest11`` entry point, so a test in another package requests ``log_manager``
or ``sink`` without declaring its own fixture.

The default manager uses ``Environment.DEV``, ``app_version="0.1.0"``, and
``app_name="billing-api"``. Pass ``log_manager.get_child_logger("Name")`` into
the component under test. Read the JSON lines with :func:`read_records`. Use
``make_manager`` only to change the level, environment, app name, app version,
or stream. Do not call ``LogManager(...)`` from a test outside this package's
own suite.
"""

import io
import json
from collections.abc import Callable
from typing import Any, BinaryIO

import pytest

from shared_config import Environment, LoggerConfig, LogLevel
from shared_log_manager.log_manager import LogManager

DEFAULT_APP_NAME = "billing-api"
DEFAULT_APP_VERSION = "0.1.0"

ManagerFactory = Callable[..., LogManager]


def read_records(stream: io.BytesIO) -> list[dict[str, Any]]:
    """Parse everything written to ``stream`` as newline-delimited JSON.

    Args:
        stream: The buffer a manager has been writing to.

    Returns:
        One dict per emitted record, in the order they were written.

    Raises:
        UnicodeDecodeError: If the output is not valid UTF-8, which is itself a failure
            worth surfacing rather than hiding behind a replacement character.
    """
    text = stream.getvalue().decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def _build_manager(
    *,
    min_level: LogLevel,
    env: Environment,
    app_name: str,
    app_version: str,
    stream: BinaryIO,
) -> LogManager:
    return LogManager(
        LoggerConfig(MIN_LOG_LEVEL=min_level),
        env=env,
        app_version=app_version,
        app_name=app_name,
        stream=stream,
    )


@pytest.fixture
def sink() -> io.BytesIO:
    """Provide an in-memory binary stream standing in for stdout.

    Returns:
        An empty buffer that a :class:`LogManager` can write records to.
    """
    return io.BytesIO()


@pytest.fixture
def log_manager(sink: io.BytesIO) -> LogManager:
    """Provide the default manager, writing to ``sink``.

    The level is ``LoggerConfig``'s own default (``info``). Tests that need
    ``debug`` use :func:`make_manager`.

    Args:
        sink: Buffer every record is written to.

    Returns:
        A manager whose records the test can inspect without touching stdout.
    """
    return _build_manager(
        min_level=LogLevel.INFO,
        env=Environment.DEV,
        app_name=DEFAULT_APP_NAME,
        app_version=DEFAULT_APP_VERSION,
        stream=sink,
    )


@pytest.fixture
def make_manager(sink: io.BytesIO) -> ManagerFactory:
    """Provide a factory for managers that differ from :func:`log_manager`.

    The first positional argument is the minimum level and defaults to ``debug``,
    so a filtering test sees every record unless it asks for a higher floor.
    ``stream`` defaults to the shared ``sink``.

    Args:
        sink: Buffer used when the caller does not pass ``stream``.

    Returns:
        A callable returning a :class:`LogManager`.
    """

    def factory(
        min_level: LogLevel = LogLevel.DEBUG,
        *,
        env: Environment = Environment.DEV,
        app_name: str = DEFAULT_APP_NAME,
        app_version: str = DEFAULT_APP_VERSION,
        stream: BinaryIO | None = None,
    ) -> LogManager:
        return _build_manager(
            min_level=min_level,
            env=env,
            app_name=app_name,
            app_version=app_version,
            stream=sink if stream is None else stream,
        )

    return factory
