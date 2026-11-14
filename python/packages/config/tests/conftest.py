"""Keep a developer shell from leaking into config assertions."""

import os

import pytest

_OWNED_PREFIXES: tuple[str, ...] = (
    "REDIS__",
    "POSTGRES__",
    "PROMETHEUS__",
    "FEATURE_FLAG__",
    "MONOREPO_ROOT",
)


def _owned(key: str) -> bool:
    upper = key.upper()
    if upper == "ENV":
        return True
    if upper.startswith(_OWNED_PREFIXES):
        return True
    return "__SERVER__" in upper or "__LOGGER__" in upper or "__MCP__" in upper


@pytest.fixture(autouse=True)
def _clear_owned_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop config variables so a developer shell cannot change assertions."""
    environ_keys = list(os.environ)
    for key in environ_keys:
        if _owned(key):
            monkeypatch.delenv(key, raising=False)
