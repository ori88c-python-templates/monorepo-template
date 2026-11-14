"""MCP path rules and the per-app MCP__ block."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared_config import (
    LIVEZ_ENDPOINT,
    METRICS_ENDPOINT,
    READYZ_ENDPOINT,
    McpConfig,
    create_mcp_config,
)


def test_defaults_are_mcp_and_sse() -> None:
    """Unset keeps the polyrepo endpoint and progress streaming."""
    config = McpConfig()
    assert config.PATH == "/mcp"
    assert config.ENABLE_SSE_STREAM_RESPONSE is True


@pytest.mark.parametrize(
    "path",
    [LIVEZ_ENDPOINT, READYZ_ENDPOINT, METRICS_ENDPOINT, "mcp", "/mcp?x=1", "/mcp#frag"],
)
def test_path_must_be_an_absolute_product_path(path: str) -> None:
    """Probe, scrape, relative, and query paths are rejected."""
    with pytest.raises(ValidationError):
        McpConfig(PATH=path)


def test_loader_is_prefixed_per_app(tmp_path: Path) -> None:
    """Two apps can expose different paths from one env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BILLING_API__MCP__PATH=/billing",
                "BILLING_API__MCP__ENABLE_SSE_STREAM_RESPONSE=false",
                "PEOPLE_API__MCP__PATH=/people",
            ]
        ),
        encoding="utf-8",
    )
    billing = create_mcp_config("billing_api", env_file=env_file)
    people = create_mcp_config("people_api", env_file=env_file)
    assert billing.PATH == "/billing"
    assert billing.ENABLE_SSE_STREAM_RESPONSE is False
    assert people.PATH == "/people"
    assert people.ENABLE_SSE_STREAM_RESPONSE is True


def test_loader_rejects_an_infrastructure_path(tmp_path: Path) -> None:
    """A prefixed PATH still cannot take /metrics."""
    env_file = tmp_path / ".env"
    env_file.write_text(f"BILLING_API__MCP__PATH={METRICS_ENDPOINT}\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        create_mcp_config("billing_api", env_file=env_file)
