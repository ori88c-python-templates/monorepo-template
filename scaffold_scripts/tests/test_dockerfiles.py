"""Dockerfile copy lines."""

from helpers.dockerfiles import use_apps_copy


def test_use_apps_copy_collapses_per_app_lines() -> None:
    """One COPY instruction replaces a list of app directories."""
    listed = (
        "COPY packages ./packages\n"
        "COPY apps/billing_api ./apps/billing_api\n"
        "COPY apps/notes_mcp ./apps/notes_mcp\n"
        "RUN true\n"
    )

    assert use_apps_copy(listed) == "COPY packages ./packages\nCOPY apps ./apps\nRUN true\n"
    assert use_apps_copy("COPY apps ./apps\n") == "COPY apps ./apps\n"
