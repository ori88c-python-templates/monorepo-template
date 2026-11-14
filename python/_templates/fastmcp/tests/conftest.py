"""Fixtures shared by unit, integration, and e2e tests.

``sink`` and ``log_manager`` come from ``shared_log_manager.testing``.
``throwaway_stores`` starts Docker only when a test requests it, so
``pytest tests/unit`` stays container-free.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.throwaway_stores import ThrowawayStores


@pytest.fixture(scope="session")
def throwaway_stores() -> Iterator[ThrowawayStores]:
    """Start throwaway Redis, then tear it down.

    Yields:
        Config pointed at the running container, not Compose.
    """
    from tests.throwaway_stores import start_throwaway_stores  # noqa: PLC0415

    with start_throwaway_stores() as stores:
        yield stores
