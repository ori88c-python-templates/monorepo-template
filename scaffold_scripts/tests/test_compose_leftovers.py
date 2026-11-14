"""Delete points at the Compose lines it does not remove."""

from pathlib import Path

from helpers.compose_leftovers import compose_leftover_lines, leftover_report
from helpers.names import AppIdentity
from helpers.operations import add_app, delete_app
from helpers.paths import read_text, write_text
from support import copied_repo

_ORDERS = AppIdentity(name="orders_api", category="fastapi", port=None)

_COMPOSE_WITH_SERVICE = """\
name: test
services:
  redis:
    image: redis:7-alpine

  migrate:
    build:
      context: ./python
      dockerfile: apps/orders_api/Dockerfile
    command: ["alembic", "upgrade", "head"]

  orders-api:
    build:
      context: ./python
      dockerfile: apps/orders_api/Dockerfile
    environment:
      ORDERS_API__SERVER__PORT: "8081"
    depends_on:
      migrate:
        condition: service_completed_successfully

  reporter:
    depends_on:
      orders-api:
        condition: service_healthy
"""


def _noop(python_dir: Path) -> None:
    assert python_dir.name == "python"


def test_leftover_lines_cover_dockerfile_prefix_and_service_tokens() -> None:
    """Each way Compose can name an app is reported, by line number."""
    lines = compose_leftover_lines(_COMPOSE_WITH_SERVICE, _ORDERS)

    assert lines == [9, 12, 15, 17, 24]


def test_a_longer_name_that_contains_the_app_is_not_a_leftover() -> None:
    """``orders_api_v2`` and ``ORDERS_API_V2__`` belong to another app."""
    text = (
        "services:\n"
        "  orders-api-v2:\n"
        "    build:\n"
        "      dockerfile: apps/orders_api_v2/Dockerfile\n"
        "    environment:\n"
        '      ORDERS_API_V2__SERVER__PORT: "8082"\n'
    )

    assert compose_leftover_lines(text, _ORDERS) == []


def test_report_names_the_app_and_the_lines() -> None:
    """The second line is one sentence an agent can act on."""
    report = leftover_report(_ORDERS, [9, 12])

    assert report == (
        "compose.yaml still references 'orders_api' on lines 9, 12. "
        "Remove the service as the scaffold skill describes."
    )


def test_delete_appends_the_report_only_when_compose_still_names_the_app(
    tmp_path: Path,
) -> None:
    """A clean Compose keeps the one-line success; a stale one gains the pointer."""
    paths = copied_repo(tmp_path)
    add_app(paths, "fastapi", "orders_api", sync=_noop)
    write_text(paths.compose_file, "name: test\nservices:\n  redis:\n    image: redis:7-alpine\n")

    assert delete_app(paths, "orders_api", sync=_noop) == "Deleted app 'orders_api'."

    add_app(paths, "fastapi", "orders_api", sync=_noop)
    write_text(paths.compose_file, _COMPOSE_WITH_SERVICE)

    message = delete_app(paths, "orders_api", sync=_noop)

    assert message.splitlines() == [
        "Deleted app 'orders_api'.",
        "compose.yaml still references 'orders_api' on lines 9, 12, 15, 17, 24. "
        "Remove the service as the scaffold skill describes.",
    ]
    assert read_text(paths.compose_file) == _COMPOSE_WITH_SERVICE
