"""The correlation id must not leak onto the next task on the event loop."""

from io import BytesIO

from httpx import AsyncClient

from shared_log_manager.testing import ManagerFactory, read_records


async def test_correlation_id_is_unbound_after_the_request(
    client: AsyncClient,
    sink: BytesIO,
    make_manager: ManagerFactory,
) -> None:
    """A child logger created after the request must not inherit ``correlation_id``."""
    await client.get("/ping")
    (during,) = read_records(sink)
    assert "correlation_id" in during

    after_sink = BytesIO()
    make_manager(stream=after_sink).get_child_logger("after").info("after.request")

    (after,) = read_records(after_sink)
    assert "correlation_id" not in after
    assert set(after) == {
        "ts",
        "msg",
        "level",
        "context",
        "env",
        "app",
        "instance",
        "app.version",
    }
