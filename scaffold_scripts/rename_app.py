"""Rename an installed app and keep its category and port."""

import argparse
from collections.abc import Sequence

from helpers.cli import fail, succeed
from helpers.errors import ScaffoldError
from helpers.operations import Sync, rename_app
from helpers.paths import RepoPaths


def main(
    argv: Sequence[str] | None = None, *, paths: RepoPaths | None = None, sync: Sync | None = None
) -> None:
    """Rename one app.

    Args:
        argv: Positional arguments, source name then target name. ``None``
            reads the process arguments.
        paths: Repository locations. ``None`` discovers them from this file.
        sync: Lock step. ``None`` runs uv.
    """
    parser = argparse.ArgumentParser(
        prog="rename_app.py",
        description="Rename an app. The category and the published port stay.",
    )
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args(argv)
    try:
        message = rename_app(paths or RepoPaths.discover(), args.source, args.target, sync=sync)
    except ScaffoldError as exc:
        fail(exc)
    succeed(message)


if __name__ == "__main__":
    main()
