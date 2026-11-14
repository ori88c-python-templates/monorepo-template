"""Copy a FastAPI, FastMCP, or task-runner template into ``python/apps`` and register it."""

import argparse
from collections.abc import Sequence

from helpers.cli import fail, succeed
from helpers.errors import ScaffoldError
from helpers.operations import Sync, add_app
from helpers.paths import RepoPaths


def main(
    argv: Sequence[str] | None = None, *, paths: RepoPaths | None = None, sync: Sync | None = None
) -> None:
    """Add one app.

    Args:
        argv: Positional arguments, ``category`` then ``name``. ``None`` reads
            the process arguments.
        paths: Repository locations. ``None`` discovers them from this file.
        sync: Lock step. ``None`` runs uv.
    """
    parser = argparse.ArgumentParser(
        prog="add_app.py",
        description=(
            "Copy a fastapi, fastmcp, or task_runner template into python/apps and register it."
        ),
    )
    parser.add_argument("category", choices=["fastapi", "fastmcp", "task_runner"])
    parser.add_argument("name")
    args = parser.parse_args(argv)
    try:
        message = add_app(paths or RepoPaths.discover(), args.category, args.name, sync=sync)
    except ScaffoldError as exc:
        fail(exc)
    succeed(message)


if __name__ == "__main__":
    main()
